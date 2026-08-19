"""Extensiones de Flask que necesitan existir antes de create_app() (para
poder importarlas desde los blueprints sin depender de la instancia app)."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
