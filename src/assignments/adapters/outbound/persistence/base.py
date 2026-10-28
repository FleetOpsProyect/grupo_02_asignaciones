"""Base declarativa compartida por los futuros modelos de SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base de la que heredaran los modelos ORM del microservicio."""
