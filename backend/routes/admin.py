"""Rutas del panel de la vendedora: login, inventario y apartados."""
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from PIL import Image
from werkzeug.utils import secure_filename
from extensions import limiter
from models import db, Usuario, Producto, Variante, Imagen, Apartado
from auth import iniciar_sesion, cerrar_sesion, usuario_actual, login_requerido
from horario import dentro_de_horario
from apartados_utils import expirar_pendientes_vencidos

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

EXTENSIONES_VALIDAS = {"png", "jpg", "jpeg", "webp"}
LADO_MAXIMO_IMAGEN = 1600


def _extension_valida(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_VALIDAS


def _guardar_imagen_comprimida(archivo, ruta_absoluta):
    """Redimensiona (si hace falta) y comprime la imagen antes de guardarla en disco."""
    try:
        imagen = Image.open(archivo.stream)
        imagen.load()
    except Exception:
        # No se pudo procesar con Pillow (archivo corrupto o formato raro):
        # se guarda tal cual llegó en vez de rechazar la subida.
        archivo.stream.seek(0)
        archivo.save(ruta_absoluta)
        return

    formato = imagen.format or "JPEG"
    if imagen.width > LADO_MAXIMO_IMAGEN or imagen.height > LADO_MAXIMO_IMAGEN:
        imagen.thumbnail((LADO_MAXIMO_IMAGEN, LADO_MAXIMO_IMAGEN), Image.LANCZOS)

    parametros_guardado = {"optimize": True}
    if formato == "JPEG":
        if imagen.mode not in ("RGB", "L"):
            imagen = imagen.convert("RGB")
        parametros_guardado["quality"] = 82

    imagen.save(ruta_absoluta, format=formato, **parametros_guardado)


@admin_bp.before_request
def _verificar_horario():
    # El panel de la vendedora también opera solo en el horario de la tienda.
    if request.method == "OPTIONS":
        return
    if request.path == "/api/admin/login" and request.method == "POST":
        return
    if not dentro_de_horario():
        return (
            jsonify({"error": "El panel solo está disponible entre 9:00 y 22:00, todos los días."}),
            403,
        )
    expirar_pendientes_vencidos()


@admin_bp.post("/login")
@limiter.limit("5 per minute")
def login():
    if not dentro_de_horario():
        return (
            jsonify({"error": "El panel solo está disponible entre 9:00 y 22:00, todos los días."}),
            403,
        )
    data = request.get_json(silent=True) or {}
    usuario = Usuario.query.filter_by(nombre_usuario=data.get("nombre_usuario", "").strip()).first()
    if not usuario or not usuario.check_password(data.get("password", "")):
        return jsonify({"error": "Usuario o contraseña incorrectos."}), 401
    iniciar_sesion(usuario)
    return jsonify(usuario.to_dict())


@admin_bp.post("/logout")
@login_requerido
def logout():
    cerrar_sesion()
    return jsonify({"ok": True})


@admin_bp.get("/me")
@login_requerido
def me():
    return jsonify(usuario_actual().to_dict())


@admin_bp.put("/password")
@login_requerido
def cambiar_password():
    usuario = usuario_actual()
    data = request.get_json(silent=True) or {}
    password_actual = data.get("password_actual") or ""
    password_nueva = data.get("password_nueva") or ""

    if not usuario.check_password(password_actual):
        return jsonify({"error": "La contraseña actual no es correcta."}), 401
    if len(password_nueva) < 8:
        return jsonify({"error": "La nueva contraseña debe tener al menos 8 caracteres."}), 400

    usuario.set_password(password_nueva)
    db.session.commit()
    return jsonify({"ok": True})


# ---------- Inventario ----------

@admin_bp.get("/productos")
@login_requerido
def listar_productos():
    productos = Producto.query.order_by(Producto.creado_en.desc()).all()
    return jsonify([p.to_dict(incluir_apartados=True) for p in productos])


@admin_bp.post("/productos")
@login_requerido
def crear_producto():
    data = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    precio = data.get("precio")
    if not nombre or precio is None:
        return jsonify({"error": "Nombre y precio son obligatorios."}), 400

    producto = Producto(
        nombre=nombre,
        descripcion=(data.get("descripcion") or "").strip(),
        categoria=(data.get("categoria") or "").strip(),
        precio=precio,
        activo=data.get("activo", True),
    )
    for v in data.get("variantes", []):
        producto.variantes.append(
            Variante(
                talla=(v.get("talla") or "").strip(),
                color=(v.get("color") or "").strip(),
                color_hex=v.get("color_hex") or "#CCCCCC",
                stock=int(v.get("stock") or 0),
            )
        )
    db.session.add(producto)
    db.session.commit()
    return jsonify(producto.to_dict()), 201


@admin_bp.put("/productos/<int:producto_id>")
@login_requerido
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    data = request.get_json(silent=True) or {}

    for campo in ("nombre", "descripcion", "categoria"):
        if campo in data:
            setattr(producto, campo, (data[campo] or "").strip())
    if "precio" in data:
        producto.precio = data["precio"]
    if "activo" in data:
        producto.activo = bool(data["activo"])

    if "variantes" in data:
        ids_recibidos = {v["id"] for v in data["variantes"] if v.get("id")}
        for variante in list(producto.variantes):
            if variante.id not in ids_recibidos:
                if variante.apartados_activos():
                    return (
                        jsonify(
                            {
                                "error": f"No se puede quitar {variante.talla} · {variante.color}: tiene apartados sin entregar."
                            }
                        ),
                        409,
                    )
                db.session.delete(variante)
        for v in data["variantes"]:
            if v.get("id"):
                variante = Variante.query.get(v["id"])
                if variante and variante.producto_id == producto.id:
                    variante.talla = (v.get("talla") or variante.talla).strip()
                    variante.color = (v.get("color") or variante.color).strip()
                    variante.color_hex = v.get("color_hex") or variante.color_hex
                    variante.stock = int(v.get("stock", variante.stock))
            else:
                producto.variantes.append(
                    Variante(
                        talla=(v.get("talla") or "").strip(),
                        color=(v.get("color") or "").strip(),
                        color_hex=v.get("color_hex") or "#CCCCCC",
                        stock=int(v.get("stock") or 0),
                    )
                )

    db.session.commit()
    return jsonify(producto.to_dict())


@admin_bp.delete("/productos/<int:producto_id>")
@login_requerido
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.post("/productos/<int:producto_id>/imagenes")
@login_requerido
def subir_imagen(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    archivo = request.files.get("imagen")
    if not archivo or archivo.filename == "":
        return jsonify({"error": "No se recibió ninguna imagen."}), 400
    if not _extension_valida(archivo.filename):
        return jsonify({"error": "Formato no válido. Usa png, jpg, jpeg o webp."}), 400

    nombre_seguro = secure_filename(archivo.filename)
    nombre_unico = f"{uuid.uuid4().hex}_{nombre_seguro}"
    ruta_absoluta = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_unico)
    _guardar_imagen_comprimida(archivo, ruta_absoluta)

    imagen = Imagen(
        producto_id=producto.id,
        url=f"/uploads/{nombre_unico}",
        orden=len(producto.imagenes),
    )
    db.session.add(imagen)
    db.session.commit()
    return jsonify(imagen.to_dict()), 201


@admin_bp.delete("/imagenes/<int:imagen_id>")
@login_requerido
def eliminar_imagen(imagen_id):
    imagen = Imagen.query.get_or_404(imagen_id)
    ruta_absoluta = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(imagen.url))
    db.session.delete(imagen)
    db.session.commit()
    try:
        if os.path.exists(ruta_absoluta):
            os.remove(ruta_absoluta)
    except OSError:
        # El registro ya se borró de la base de datos; si el archivo físico
        # no se pudo eliminar (permisos del disco), no debe tumbar la petición.
        pass
    return jsonify({"ok": True})


# ---------- Apartados ----------

@admin_bp.get("/apartados")
@login_requerido
def listar_apartados():
    estado = request.args.get("estado")
    query = Apartado.query
    if estado:
        query = query.filter_by(estado=estado)
    apartados = query.order_by(Apartado.fecha_apartado.desc()).all()
    return jsonify([a.to_dict() for a in apartados])


ESTADOS_VALIDOS = {"pendiente", "confirmado", "entregado", "cancelado"}
ESTADOS_ACTIVOS = {"pendiente", "confirmado"}


@admin_bp.put("/apartados/<int:apartado_id>")
@login_requerido
def actualizar_apartado(apartado_id):
    apartado = Apartado.query.get_or_404(apartado_id)
    data = request.get_json(silent=True) or {}
    nuevo_estado = data.get("estado")

    if nuevo_estado not in ESTADOS_VALIDOS:
        return jsonify({"error": "Estado no válido."}), 400

    estado_anterior = apartado.estado
    variante = apartado.variante

    if nuevo_estado != estado_anterior:
        # La existencia física solo se mueve cuando la prenda de verdad
        # entra o sale de las manos de la vendedora (se entrega o se
        # regresa tras haberse entregado).
        if nuevo_estado == "entregado" and estado_anterior != "entregado":
            if variante.stock <= 0:
                return jsonify({"error": "No queda existencia física para entregar esta prenda."}), 409
            variante.stock -= 1
        elif estado_anterior == "entregado" and nuevo_estado != "entregado":
            variante.stock += 1

        # Si se reactiva un apartado (de cancelado/entregado a
        # pendiente/confirmado) hay que confirmar que sigue habiendo
        # existencia disponible para comprometerla de nuevo.
        if nuevo_estado in ESTADOS_ACTIVOS and estado_anterior not in ESTADOS_ACTIVOS:
            otros_activos = len(variante.apartados_activos(excluir_id=apartado.id))
            if variante.stock - otros_activos <= 0:
                return jsonify({"error": "Ya no hay existencia disponible para reactivar este apartado."}), 409

    apartado.estado = nuevo_estado
    if "notas" in data:
        apartado.notas = data["notas"]
    db.session.commit()
    return jsonify(apartado.to_dict())
