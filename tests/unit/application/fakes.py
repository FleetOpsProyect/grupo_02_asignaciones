"""Dobles de prueba de los puertos de application/, usados por las pruebas de casos de uso."""

from __future__ import annotations

import uuid
from datetime import date

from assignments.application.errors import ExternalServiceUnavailableError
from assignments.application.ports.assignment_repository import AssignmentFilters
from assignments.domain.assignment import Assignment, AssignmentStatus

_ACTIVE_STATUSES = (AssignmentStatus.PENDIENTE, AssignmentStatus.EN_CURSO)


class FakeAssignmentRepository:
    """Repositorio en memoria: suficiente para probar los casos de uso sin Postgres."""

    def __init__(self, assignments: list[Assignment] | None = None) -> None:
        self._assignments: list[Assignment] = list(assignments or [])

    def add(self, assignment: Assignment) -> None:
        self._assignments.append(assignment)

    def get_by_id(self, assignment_id: uuid.UUID) -> Assignment | None:
        return next((a for a in self._assignments if a.id == assignment_id), None)

    def search(
        self, filters: AssignmentFilters, page: int, size: int
    ) -> tuple[list[Assignment], int]:
        matches = [a for a in self._assignments if self._matches(a, filters)]
        start = (page - 1) * size
        return matches[start : start + size], len(matches)

    def count_by_status(self, filters: AssignmentFilters) -> dict[AssignmentStatus, int]:
        unrestricted = AssignmentFilters(
            employee_id=filters.employee_id,
            driver_id=filters.driver_id,
            vehicle_id=filters.vehicle_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
        )
        summary: dict[AssignmentStatus, int] = dict.fromkeys(AssignmentStatus, 0)
        for assignment in self._assignments:
            if self._matches(assignment, unrestricted):
                summary[assignment.status] += 1
        return summary

    def busy_vehicle_ids(
        self, vehicle_ids: list[str], start_date: date, end_date: date
    ) -> set[str]:
        return {
            a.vehicle_id
            for a in self._assignments
            if a.vehicle_id in vehicle_ids
            and a.status in _ACTIVE_STATUSES
            and self._overlaps(a, start_date, end_date)
        }

    def busy_driver_ids(self, driver_ids: list[str], start_date: date, end_date: date) -> set[str]:
        return {
            a.driver_id
            for a in self._assignments
            if a.driver_id in driver_ids
            and a.status in _ACTIVE_STATUSES
            and self._overlaps(a, start_date, end_date)
        }

    @staticmethod
    def _overlaps(assignment: Assignment, start_date: date, end_date: date) -> bool:
        return assignment.start_date <= end_date and assignment.end_date >= start_date

    @staticmethod
    def _matches(assignment: Assignment, filters: AssignmentFilters) -> bool:
        if filters.statuses is not None and assignment.status not in filters.statuses:
            return False
        if filters.employee_id is not None and assignment.employee_id != filters.employee_id:
            return False
        if filters.driver_id is not None and assignment.driver_id != filters.driver_id:
            return False
        if filters.vehicle_id is not None and assignment.vehicle_id != filters.vehicle_id:
            return False
        if filters.start_date is not None and assignment.start_date < filters.start_date:
            return False
        if filters.end_date is not None and assignment.end_date > filters.end_date:
            return False
        return True


class FakeVehicleDirectory:
    """Doble del puerto hacia el servicio de Vehiculos."""

    def __init__(self, active_ids: list[str] | None = None, unavailable: bool = False) -> None:
        self._active_ids = active_ids or []
        self._unavailable = unavailable

    def find_active(self, vehicle_type: str, valid_until: date) -> list[str]:
        if self._unavailable:
            raise ExternalServiceUnavailableError("Vehiculos no responde")
        return list(self._active_ids)


class FakeDriverDirectory:
    """Doble del puerto hacia el servicio de Conductores."""

    def __init__(self, active_ids: list[str] | None = None, unavailable: bool = False) -> None:
        self._active_ids = active_ids or []
        self._unavailable = unavailable

    def find_active(self, valid_until: date) -> list[str]:
        if self._unavailable:
            raise ExternalServiceUnavailableError("Conductores no responde")
        return list(self._active_ids)


class FakeEventPublisher:
    """Doble del publicador de eventos: registra lo publicado para verificarlo."""

    def __init__(self) -> None:
        self.published: list[Assignment] = []

    def assignment_created(self, assignment: Assignment) -> None:
        self.published.append(assignment)
