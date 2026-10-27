"""Verificacion de disponibilidad de Redis para el endpoint /ready."""

import redis


def build_cache_health_check(client: redis.Redis | None) -> "CacheHealthCheck | None":
    """Crea la verificacion de salud de Redis, o None si no hay cliente configurado."""
    if client is None:
        return None
    return CacheHealthCheck(client)


class CacheHealthCheck:
    """Ejecuta un PING contra Redis para confirmar que responde."""

    name = "cache"

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def __call__(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:
            return False
