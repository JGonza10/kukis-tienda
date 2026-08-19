"""Aviso a la vendedora por Telegram cuando entra un apartado nuevo.

Es una integración opcional: si TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no
están configurados, o si Telegram no responde, la creación del apartado
nunca debe fallar por esto.
"""
import os

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def notificar_nuevo_apartado(apartado):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    producto = apartado.variante.producto if apartado.variante else None
    mensaje = (
        "🧵 Nuevo apartado\n"
        f"Prenda: {producto.nombre if producto else '—'}\n"
        f"Talla/color: {apartado.variante.talla} · {apartado.variante.color}\n"
        f"Clienta: {apartado.cliente_nombre}\n"
        f"Teléfono: {apartado.cliente_telefono}\n"
        f"Entrega: {apartado.fecha_entrega.isoformat() if apartado.fecha_entrega else '—'}"
    )

    try:
        requests.post(
            TELEGRAM_API.format(token=token),
            json={"chat_id": chat_id, "text": mensaje},
            timeout=5,
        )
    except requests.RequestException:
        # Un fallo de red o de Telegram no debe tumbar la creación del apartado.
        pass
