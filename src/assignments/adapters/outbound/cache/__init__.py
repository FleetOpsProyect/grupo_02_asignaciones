"""Conexion a Redis; solo lo necesario para que /ready pueda verificarla."""

from assignments.adapters.outbound.cache.client import build_redis_client
from assignments.adapters.outbound.cache.health import build_cache_health_check

__all__ = ["build_redis_client", "build_cache_health_check"]
