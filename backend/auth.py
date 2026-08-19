"""Login de la vendedora basado en sesión de Flask (una sola cuenta admin)."""
from functools import wraps
from flask import session, jsonify
from models import Usuario


def iniciar_sesion(usuario):
    session["usuario_id"] = usuario.id
    session.permanent = True


def cerrar_sesion():
    session.pop("usuario_id", None)


def usuario_actual():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return None
    return Usuario.query.get(usuario_id)


def login_requerido(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not usuario_actual():
            return jsonify({"error": "Debes iniciar sesión."}), 401
        return fn(*args, **kwargs)

    return wrapper
