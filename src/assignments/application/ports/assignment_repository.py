"""Puerto que `application/` necesita para persistir y consultar asignaciones."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from assignments.domain.assignment import Assignment, AssignmentStatus


@dataclass(frozen=True)
class AssignmentFilters:
    """Filtros opcionales soportados por GET /assignment y GET /assignment/active.

    `statuses=None` significa "cualquier estado". GET /assignment/active lo usa
    con `{PENDIENTE, EN_CURSO}` por defecto, para restringir a asignaciones activas.
    """

    statuses: frozenset[AssignmentStatus] | None = None
    employee_id: str | None = None
    driver_id: str | None = None
    vehicle_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class AssignmentRepository(Protocol):
    """Puerto de persistencia de asignaciones. Lo implementa un adapter outbound."""

    def add(self, assignment: Assignment) -> None:
        """Guarda una asignacion nueva."""
        ...

    def get_by_id(self, assignment_id: uuid.UUID) -> Assignment | None:
        """Busca una asignacion por id; None si no existe."""
        ...

    def search(
        self, filters: AssignmentFilters, page: int, size: int
    ) -> tuple[list[Assignment], int]:
        """Lista asignaciones que cumplen los filtros, paginadas.

        Devuelve la pagina solicitada y el total de registros que cumplen
        los filtros (sin paginar), para construir la metadata de paginacion.
        """
        ...

    def count_by_status(self, filters: AssignmentFilters) -> dict[AssignmentStatus, int]:
        """Cuenta cuantas asignaciones hay por estado, aplicando los filtros.

        Ignora `filters.statuses` para mostrar el desglose completo de todos los
        estados posibles dentro de ese subconjunto, aunque la consulta original
        ya este filtrada por uno o varios estados.
        """
        ...

    def busy_vehicle_ids(
        self, vehicle_ids: list[str], start_date: date, end_date: date
    ) -> set[str]:
        """De los vehiculos candidatos, cuales ya tienen una asignacion activa que se cruza."""
        ...

    def busy_driver_ids(self, driver_ids: list[str], start_date: date, end_date: date) -> set[str]:
        """De los conductores candidatos, cuales ya tienen una asignacion activa que se cruza."""
        ...
