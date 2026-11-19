"""Errores de la capa de aplicacion (no son reglas de negocio del dominio)."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base de los errores propios de la orquestacion de casos de uso."""


class ExternalServiceUnavailableError(ApplicationError):
    """Un servicio externo necesario para el caso de uso no respondio (p. ej. Vehiculos)."""
