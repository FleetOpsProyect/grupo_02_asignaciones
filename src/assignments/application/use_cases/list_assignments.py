"""Caso de uso: listar asignaciones con filtros, paginacion y resumen por estado.

Lo usan tanto GET /assignment (todos los estados) como GET /assignment/active
(solo PENDIENTE/EN_CURSO): el endpoint decide los `filters`, este caso de uso
solo orquesta la consulta paginada y el conteo por estado.
"""

from __future__ import annotations

from dataclasses import dataclass

from assignments.application.ports.assignment_repository import (
    AssignmentFilters,
    AssignmentRepository,
)
from assignments.domain.assignment import Assignment, AssignmentStatus


@dataclass(frozen=True)
class AssignmentPage:
    """Resultado paginado de una consulta de asignaciones."""

    items: list[Assignment]
    total: int
    page: int
    size: int
    summary: dict[AssignmentStatus, int]


class ListAssignmentsUseCase:
    """Orquesta la busqueda paginada y el resumen por estado."""

    def __init__(self, repository: AssignmentRepository) -> None:
        self._repository = repository

    def execute(self, filters: AssignmentFilters, page: int, size: int) -> AssignmentPage:
        items, total = self._repository.search(filters, page, size)
        summary = self._repository.count_by_status(filters)
        return AssignmentPage(items=items, total=total, page=page, size=size, summary=summary)
