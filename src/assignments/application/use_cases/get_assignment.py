"""Caso de uso: consultar una asignacion por id."""

from __future__ import annotations

import uuid

from assignments.application.ports.assignment_repository import AssignmentRepository
from assignments.domain.assignment import Assignment
from assignments.domain.exceptions import AssignmentNotFoundError


class GetAssignmentUseCase:
    """Devuelve una asignacion por id, o lanza AssignmentNotFoundError si no existe."""

    def __init__(self, repository: AssignmentRepository) -> None:
        self._repository = repository

    def execute(self, assignment_id: uuid.UUID) -> Assignment:
        assignment = self._repository.get_by_id(assignment_id)
        if assignment is None:
            raise AssignmentNotFoundError(f"No existe la asignacion {assignment_id}")
        return assignment
