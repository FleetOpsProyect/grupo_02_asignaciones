"""Publicador de eventos de asignaciones.

El broker de eventos (Kafka o RabbitMQ) todavia no esta acordado entre los
equipos de FleetOps. Mientras tanto, este adapter solo deja constancia del
evento en el log estructurado del servicio, con los mismos datos que tendria
el evento real, para no bloquear el resto de la implementacion. Cuando se
decida el broker, se agrega un adapter nuevo que publique de verdad y
cumpla el mismo puerto `AssignmentEventPublisher`, sin tocar `application/`.
"""

from __future__ import annotations

import logging

from assignments.domain.assignment import Assignment

logger = logging.getLogger(__name__)


class LoggingAssignmentEventPublisher:
    """Implementacion provisional de AssignmentEventPublisher: solo registra en el log."""

    def assignment_created(self, assignment: Assignment) -> None:
        logger.info(
            "assignment_created_event",
            extra={
                "event": "assignment_created_event",
                "assignment_id": str(assignment.id),
                "employee_id": assignment.employee_id,
                "vehicle_id": assignment.vehicle_id,
                "driver_id": assignment.driver_id,
                "vehicle_type": assignment.vehicle_type,
                "start_date": assignment.start_date.isoformat(),
                "end_date": assignment.end_date.isoformat(),
            },
        )
