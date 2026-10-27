"""Construccion del engine y la fabrica de sesiones de SQLAlchemy."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from assignments.config import Settings


def build_engine(settings: Settings) -> Engine:
    """Crea el engine de SQLAlchemy a partir de la configuracion del servicio."""
    return create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        pool_timeout=settings.database_pool_timeout_seconds,
        pool_pre_ping=True,
    )


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Crea la fabrica de sesiones ligada al engine dado."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
