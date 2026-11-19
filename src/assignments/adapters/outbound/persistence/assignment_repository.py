"""Adapter de persistencia: implementa AssignmentRepository sobre PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from assignments.adapters.outbound.persistence.models import AssignmentModel
from assignments.application.ports.assignment_repository import AssignmentFilters
from assignments.domain.assignment import Assignment, AssignmentStatus

_ACTIVE_STATUS_VALUES = [AssignmentStatus.PENDIENTE.value, AssignmentStatus.EN_CURSO.value]


class SqlAlchemyAssignmentRepository:
    """Implementacion del puerto `AssignmentRepository` sobre PostgreSQL."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, assignment: Assignment) -> None:
        with self._session_factory() as session:
            session.add(_to_model(assignment))
            session.commit()

    def get_by_id(self, assignment_id: uuid.UUID) -> Assignment | None:
        with self._session_factory() as session:
            model = session.get(AssignmentModel, assignment_id)
            return _to_entity(model) if model is not None else None

    def search(
        self, filters: AssignmentFilters, page: int, size: int
    ) -> tuple[list[Assignment], int]:
        with self._session_factory() as session:
            base_stmt = _apply_filters(select(AssignmentModel), filters)
            total = session.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
            paged_stmt = (
                base_stmt.order_by(AssignmentModel.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
            models = session.scalars(paged_stmt).all()
            return [_to_entity(model) for model in models], total

    def count_by_status(self, filters: AssignmentFilters) -> dict[AssignmentStatus, int]:
        unrestricted = AssignmentFilters(
            employee_id=filters.employee_id,
            driver_id=filters.driver_id,
            vehicle_id=filters.vehicle_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
        )
        with self._session_factory() as session:
            stmt = _apply_filters(
                select(AssignmentModel.status, func.count()).group_by(AssignmentModel.status),
                unrestricted,
            )
            counts = {AssignmentStatus(status): count for status, count in session.execute(stmt)}
            return {status: counts.get(status, 0) for status in AssignmentStatus}

    def busy_vehicle_ids(
        self, vehicle_ids: list[str], start_date: date, end_date: date
    ) -> set[str]:
        if not vehicle_ids:
            return set()
        with self._session_factory() as session:
            stmt = select(AssignmentModel.vehicle_id).where(
                AssignmentModel.vehicle_id.in_(vehicle_ids),
                AssignmentModel.status.in_(_ACTIVE_STATUS_VALUES),
                AssignmentModel.start_date <= end_date,
                AssignmentModel.end_date >= start_date,
            )
            return set(session.scalars(stmt).all())

    def busy_driver_ids(self, driver_ids: list[str], start_date: date, end_date: date) -> set[str]:
        if not driver_ids:
            return set()
        with self._session_factory() as session:
            stmt = select(AssignmentModel.driver_id).where(
                AssignmentModel.driver_id.in_(driver_ids),
                AssignmentModel.status.in_(_ACTIVE_STATUS_VALUES),
                AssignmentModel.start_date <= end_date,
                AssignmentModel.end_date >= start_date,
            )
            return set(session.scalars(stmt).all())


def _apply_filters(stmt: Any, filters: AssignmentFilters) -> Any:
    """Agrega las clausulas WHERE de `filters` a `stmt` (select de 1 o varias columnas)."""
    if filters.statuses is not None:
        stmt = stmt.where(AssignmentModel.status.in_([status.value for status in filters.statuses]))
    if filters.employee_id is not None:
        stmt = stmt.where(AssignmentModel.employee_id == filters.employee_id)
    if filters.driver_id is not None:
        stmt = stmt.where(AssignmentModel.driver_id == filters.driver_id)
    if filters.vehicle_id is not None:
        stmt = stmt.where(AssignmentModel.vehicle_id == filters.vehicle_id)
    if filters.start_date is not None:
        stmt = stmt.where(AssignmentModel.start_date >= filters.start_date)
    if filters.end_date is not None:
        stmt = stmt.where(AssignmentModel.end_date <= filters.end_date)
    return stmt


def _to_model(assignment: Assignment) -> AssignmentModel:
    return AssignmentModel(
        id=assignment.id,
        employee_id=assignment.employee_id,
        vehicle_id=assignment.vehicle_id,
        driver_id=assignment.driver_id,
        vehicle_type=assignment.vehicle_type,
        status=assignment.status.value,
        start_date=assignment.start_date,
        end_date=assignment.end_date,
        origin=assignment.origin,
        destination=assignment.destination,
        created_at=assignment.created_at,
    )


def _to_entity(model: AssignmentModel) -> Assignment:
    return Assignment(
        id=model.id,
        employee_id=model.employee_id,
        vehicle_id=model.vehicle_id,
        driver_id=model.driver_id,
        vehicle_type=model.vehicle_type,
        status=AssignmentStatus(model.status),
        start_date=model.start_date,
        end_date=model.end_date,
        origin=model.origin,
        destination=model.destination,
        created_at=model.created_at,
    )
