"""Application factory de la tienda Kukis.

En producción (Railway) este mismo servicio sirve la API (/api/...), las
imágenes subidas (/uploads/...) y el build de React (frontend/dist) para no
necesitar dos servicios separados. En desarrollo, Vite corre aparte y le
hace proxy a /api y /uploads (ver frontend/vite.config.js).
"""
import os
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from models import db, Usuario
from extensions import limiter

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))


def _variable_obligatoria(nombre):
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(
            f"Falta la variable de entorno {nombre}. Revisa backend/.env.example."
        )
    return valor


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = _variable_obligatoria("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'kukis.db')}"
    ).replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB por imagen
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Solo exigimos cookie de sesión sobre HTTPS cuando ya se sirve el build
    # de React (es decir, en el despliegue real): en desarrollo local el
    # backend corre en http:// y el navegador descartaría la cookie.
    app.config["SESSION_COOKIE_SECURE"] = os.path.isdir(FRONTEND_DIST)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    db.init_app(app)
    limiter.init_app(app)

    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
    CORS(app, supports_credentials=True, origins=[frontend_origin])

    from routes.publico import publico_bp
    from routes.admin import admin_bp

    app.register_blueprint(publico_bp)
    app.register_blueprint(admin_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "servicio": "kukis-tienda"})

    @app.get("/uploads/<path:nombre_archivo>")
    def uploads(nombre_archivo):
        return send_from_directory(UPLOAD_FOLDER, nombre_archivo)

    if os.path.isdir(FRONTEND_DIST):
        @app.get("/")
        @app.get("/<path:ruta>")
        def frontend(ruta=""):
            archivo_solicitado = os.path.join(FRONTEND_DIST, ruta)
            if ruta and os.path.isfile(archivo_solicitado):
                return send_from_directory(FRONTEND_DIST, ruta)
            return send_from_directory(FRONTEND_DIST, "index.html")

    with app.app_context():
        db.create_all()
        if not Usuario.query.first():
            vendedora = Usuario(
                nombre_usuario=os.environ.get("NOMBRE_USUARIO_INICIAL", "vendedora"),
                nombre="Vendedora",
            )
            vendedora.set_password(_variable_obligatoria("PASSWORD_INICIAL"))
            db.session.add(vendedora)
            db.session.commit()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
