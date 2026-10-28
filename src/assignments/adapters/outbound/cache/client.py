"""Construccion del cliente de Redis; el servicio arranca igual si no esta configurado."""

import redis

from assignments.config import Settings


def build_redis_client(settings: Settings) -> redis.Redis | None:
    """Crea el cliente de Redis si REDIS_URL esta configurado; None en caso contrario."""
    if not settings.redis_url:
        return None
    return redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
