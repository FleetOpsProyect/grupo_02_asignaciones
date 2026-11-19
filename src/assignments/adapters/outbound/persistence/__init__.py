"""Motor y sesion de SQLAlchemy, la Base declarativa y los modelos del servicio.

Los modelos se importan aqui (y no solo donde se usan) para que queden
registrados en `Base.metadata` antes de que Alembic autogenere migraciones.
"""

from assignments.adapters.outbound.persistence.assignment_repository import (
    SqlAlchemyAssignmentRepository,
)
from assignments.adapters.outbound.persistence.base import Base
from assignments.adapters.outbound.persistence.engine import build_engine, build_session_factory
from assignments.adapters.outbound.persistence.models import AssignmentModel

__all__ = [
    "AssignmentModel",
    "Base",
    "SqlAlchemyAssignmentRepository",
    "build_engine",
    "build_session_factory",
]
