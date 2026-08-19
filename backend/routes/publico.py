"""Rutas públicas: catálogo, ficha de producto y crear un apartado."""
from flask import Blueprint, request, jsonify
from models import db, Producto, Variante, Apartado
from horario import dentro_de_horario, estado_horario
from apartados_utils import expirar_pendientes_vencidos
from notificaciones import notificar_nuevo_apartado

publico_bp = Blueprint("publico", __name__, url_prefix="/api")


@publico_bp.get("/horario")
def horario():
    return jsonify(estado_horario())


@publico_bp.get("/productos")
def listar_productos():
    expirar_pendientes_vencidos()
    productos = (
        Producto.query.filter_by(activo=True).order_by(Producto.creado_en.desc()).all()
    )
    return jsonify([p.to_dict() for p in productos])


@publico_bp.get("/productos/<int:producto_id>")
def ver_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if not producto.activo:
        return jsonify({"error": "Esta prenda ya no está disponible."}), 404
    return jsonify(producto.to_dict())


@publico_bp.post("/apartados")
def crear_apartado():
    if not dentro_de_horario():
        return (
            jsonify(
                {
                    "error": "Los apartados solo se pueden hacer entre 9:00 y 22:00, todos los días."
                }
            ),
            403,
        )

    data = request.get_json(silent=True) or {}
    variante_id = data.get("variante_id")
    cliente_nombre = (data.get("cliente_nombre") or "").strip()
    cliente_telefono = (data.get("cliente_telefono") or "").strip()
    notas = (data.get("notas") or "").strip()

    if not variante_id or not cliente_nombre or not cliente_telefono:
        return jsonify({"error": "Faltan datos: talla/color, nombre y teléfono son obligatorios."}), 400

    variante = Variante.query.get(variante_id)
    if not variante or not variante.producto.activo:
        return jsonify({"error": "Esa prenda ya no está disponible."}), 404

    if variante.disponible() <= 0:
        return jsonify({"error": "Ya no hay existencia de esa talla y color."}), 409

    apartado = Apartado(
        variante_id=variante.id,
        cliente_nombre=cliente_nombre,
        cliente_telefono=cliente_telefono,
        notas=notas,
        estado="pendiente",
    )
    db.session.add(apartado)
    db.session.commit()
    notificar_nuevo_apartado(apartado)

    return jsonify(apartado.to_dict()), 201
