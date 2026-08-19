"""Control del horario de operación de la tienda: todos los días, 9:00-22:00.

Usa la zona horaria de Ciudad de México para que el horario tenga sentido
sin importar en qué servidor/zona corra Railway.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("America/Mexico_City")
HORA_APERTURA = 9
HORA_CIERRE = 22


def ahora_cdmx():
    return datetime.now(ZONA)


def dentro_de_horario(momento=None):
    momento = momento or ahora_cdmx()
    return HORA_APERTURA <= momento.hour < HORA_CIERRE


def estado_horario():
    momento = ahora_cdmx()
    return {
        "abierto": dentro_de_horario(momento),
        "hora_actual": momento.strftime("%H:%M"),
        "apertura": f"{HORA_APERTURA:02d}:00",
        "cierre": f"{HORA_CIERRE:02d}:00",
    }
