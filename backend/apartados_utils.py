"""Limpieza de apartados abandonados.

Sin scheduler externo: se invoca de forma oportunista en cada visita al
catálogo público y en cada acción del panel (ver el before_request de
routes/admin.py y listar_productos en routes/publico.py), suficiente para el
volumen de una tienda de tianguis.
"""
import os
from datetime import datetime, timedelta

from models import db, Apartado

HORAS_EXPIRACION_DEFAULT = 24


def _horas_expiracion():
    try:
        return float(os.environ.get("APARTADO_HORAS_EXPIRACION", HORAS_EXPIRACION_DEFAULT))
    except ValueError:
        return HORAS_EXPIRACION_DEFAULT


def expirar_pendientes_vencidos():
    """Cancela los apartados 'pendiente' que llevan demasiado tiempo sin confirmarse,
    para liberar el stock que estaban comprometiendo."""
    corte = datetime.utcnow() - timedelta(hours=_horas_expiracion())
    vencidos = Apartado.query.filter(
        Apartado.estado == "pendiente", Apartado.fecha_apartado < corte
    ).all()
    if not vencidos:
        return

    nota_auto = f"[Auto] Cancelado por falta de confirmación tras {_horas_expiracion():g}h."
    for apartado in vencidos:
        apartado.estado = "cancelado"
        apartado.notas = f"{apartado.notas}\n{nota_auto}".strip() if apartado.notas else nota_auto
    db.session.commit()
