"""Modelo SQLAlchemy de la tabla `assignments`."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from assignments.adapters.outbound.persistence.base import Base


class AssignmentModel(Base):
    """Fila de `assignments`. Ningun registro se elimina, solo cambia `status`."""

    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_id: Mapped[str] = mapped_column(String(64), index=True)
    driver_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date, index=True)
    origin: Mapped[str | None] = mapped_column(String(255))
    destination: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
