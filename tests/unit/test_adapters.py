"""Pruebas unitarias de los adapters de infraestructura."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from assignments.adapters.outbound.cache.client import build_redis_client
from assignments.adapters.outbound.cache.health import (
    CacheHealthCheck,
    build_cache_health_check,
)
from assignments.adapters.outbound.persistence.engine import (
    build_engine,
    build_session_factory,
)
from assignments.adapters.outbound.persistence.health import (
    DatabaseHealthCheck,
    build_database_health_check,
)
from assignments.config import Settings


def test_build_redis_client_returns_none_without_url() -> None:
    settings = Settings(database_url="postgresql://unused")

    assert build_redis_client(settings) is None


def test_build_redis_client_uses_configured_url() -> None:
    settings = Settings(database_url="postgresql://unused", redis_url="redis://cache:6379/0")

    with patch("assignments.adapters.outbound.cache.client.redis.Redis.from_url") as from_url:
        client = build_redis_client(settings)

    from_url.assert_called_once_with(
        "redis://cache:6379/0",
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    assert client is from_url.return_value


def test_cache_health_check_builder_and_ping() -> None:
    redis_client = MagicMock()
    redis_client.ping.return_value = True

    assert build_cache_health_check(None) is None
    health_check = build_cache_health_check(redis_client)

    assert isinstance(health_check, CacheHealthCheck)
    assert health_check() is True


def test_cache_health_check_returns_false_when_ping_fails() -> None:
    redis_client = MagicMock()
    redis_client.ping.side_effect = RuntimeError("unavailable")

    assert CacheHealthCheck(redis_client)() is False


def test_database_health_check_builder_and_query() -> None:
    connection = MagicMock()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection

    health_check = build_database_health_check(engine)

    assert isinstance(health_check, DatabaseHealthCheck)
    assert health_check() is True
    connection.execute.assert_called_once()


def test_database_health_check_returns_false_when_connection_fails() -> None:
    engine = MagicMock()
    engine.connect.side_effect = RuntimeError("unavailable")

    assert DatabaseHealthCheck(engine)() is False


def test_build_engine_and_session_factory() -> None:
    settings = Settings(database_url="postgresql://unused")

    with patch("assignments.adapters.outbound.persistence.engine.create_engine") as create_engine:
        engine = build_engine(settings)

    create_engine.assert_called_once_with(
        "postgresql://unused",
        pool_size=5,
        pool_timeout=5,
        pool_pre_ping=True,
    )
    factory = build_session_factory(engine)

    assert factory.kw["bind"] is engine
    assert factory.kw["autoflush"] is False
    assert factory.kw["expire_on_commit"] is False
