"""Errores de negocio del dominio de Asignaciones."""

from __future__ import annotations


class DomainError(Exception):
    """Base de cualquier error de negocio de este microservicio."""


class InvalidAssignmentRequestError(DomainError):
    """La solicitud de asignacion no cumple una regla de negocio (p. ej. fechas)."""


class InvalidTransitionError(DomainError):
    """Se intento una transicion de estado que la maquina de estados no permite."""


class AssignmentNotFoundError(DomainError):
    """No existe una asignacion con el id solicitado."""


class NoAvailabilityError(DomainError):
    """No hay vehiculo y conductor aptos y libres para el periodo solicitado."""
