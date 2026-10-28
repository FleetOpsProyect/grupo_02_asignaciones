"""Verificacion de disponibilidad de PostgreSQL para el endpoint /ready."""

from sqlalchemy import Engine, text


def build_database_health_check(engine: Engine) -> "DatabaseHealthCheck":
    """Crea la verificacion de salud de la base de datos para un engine dado."""
    return DatabaseHealthCheck(engine)


class DatabaseHealthCheck:
    """Ejecuta un SELECT 1 contra PostgreSQL para confirmar que responde."""

    name = "database"

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def __call__(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
