"""Limitador de tasa compartido por los endpoints HTTP.

Se define aqui, aparte de `main.py`, para que los blueprints puedan decorar
sus vistas con `@limiter.limit(...)` sin crear un import circular: main.py
es quien lo inicializa de verdad contra la app con `limiter.init_app(app)`.
"""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
