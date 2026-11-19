"""Publicador de eventos propios del microservicio (assignment_created_event y similares)."""

from assignments.adapters.outbound.messaging.event_publisher import (
    LoggingAssignmentEventPublisher,
)

__all__ = ["LoggingAssignmentEventPublisher"]
