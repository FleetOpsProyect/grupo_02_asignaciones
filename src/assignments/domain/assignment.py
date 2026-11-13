"""Entidad Asignacion y su maquina de estados. No depende de Flask, SQLAlchemy ni Redis."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum

from assignments.domain.exceptions import InvalidAssignmentRequestError, InvalidTransitionError


class AssignmentStatus(StrEnum):
    """Estados posibles de una asignacion, segun el ciclo de vida documentado."""

    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    FINALIZADA = "FINALIZADA"
    INTERRUMPIDA_POR_INCIDENTE = "INTERRUMPIDA_POR_INCIDENTE"


_ACTIVE_STATUSES = (AssignmentStatus.PENDIENTE, AssignmentStatus.EN_CURSO)


@dataclass
class Assignment:
    """Asignacion de un vehiculo y un conductor a un empleado durante un periodo.

    Ningun registro se elimina: solo cambia de estado a traves de los metodos
    `start`, `finish` e `interrupt`, que validan la transicion.
    """

    id: uuid.UUID
    employee_id: str
    vehicle_id: str
    driver_id: str
    vehicle_type: str
    start_date: date
    end_date: date
    status: AssignmentStatus
    created_at: datetime
    origin: str | None = field(default=None)
    destination: str | None = field(default=None)

    @classmethod
    def request(
        cls,
        *,
        employee_id: str,
        vehicle_id: str,
        driver_id: str,
        vehicle_type: str,
        start_date: date,
        end_date: date,
    ) -> Assignment:
        """Crea una nueva asignacion en estado PENDIENTE a partir de una solicitud."""
        if end_date <= start_date:
            raise InvalidAssignmentRequestError(
                "end_date debe ser posterior a start_date",
            )
        return cls(
            id=uuid.uuid4(),
            employee_id=employee_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            vehicle_type=vehicle_type,
            start_date=start_date,
            end_date=end_date,
            status=AssignmentStatus.PENDIENTE,
            created_at=datetime.now(UTC),
        )

    def is_active(self) -> bool:
        """Indica si la asignacion sigue en curso (PENDIENTE o EN_CURSO)."""
        return self.status in _ACTIVE_STATUSES

    def start(self) -> None:
        """Transicion disparada por RutaIniciadaEvent."""
        self._ensure_transition_from(AssignmentStatus.PENDIENTE, AssignmentStatus.EN_CURSO)
        self.status = AssignmentStatus.EN_CURSO

    def finish(self) -> None:
        """Transicion disparada por RutaFinalizadaEvent."""
        self._ensure_transition_from(AssignmentStatus.EN_CURSO, AssignmentStatus.FINALIZADA)
        self.status = AssignmentStatus.FINALIZADA

    def interrupt(self) -> None:
        """Transicion disparada por un evento de incidente."""
        self._ensure_transition_from(
            AssignmentStatus.EN_CURSO, AssignmentStatus.INTERRUMPIDA_POR_INCIDENTE
        )
        self.status = AssignmentStatus.INTERRUMPIDA_POR_INCIDENTE

    def _ensure_transition_from(self, expected: AssignmentStatus, target: AssignmentStatus) -> None:
        if self.status != expected:
            raise InvalidTransitionError(
                f"No se puede pasar de {self.status} a {target} (se esperaba estar en {expected})"
            )
