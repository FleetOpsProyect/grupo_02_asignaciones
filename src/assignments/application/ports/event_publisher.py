"""Puerto para publicar los eventos de dominio de Asignaciones.

El broker (Kafka o RabbitMQ) todavia no esta acordado entre los equipos, asi
que por ahora el unico adapter concreto solo registra el evento en el log
(ver `adapters/outbound/messaging`). Cuando se decida el broker, se agrega un
adapter nuevo que implemente este mismo puerto, sin tocar los casos de uso.
"""

from __future__ import annotations

from typing import Protocol

from assignments.domain.assignment import Assignment


class AssignmentEventPublisher(Protocol):
    """Puerto de publicacion de eventos de asignaciones."""

    def assignment_created(self, assignment: Assignment) -> None:
        """Publica `assignment_created_event` tras crear una asignacion."""
        ...
