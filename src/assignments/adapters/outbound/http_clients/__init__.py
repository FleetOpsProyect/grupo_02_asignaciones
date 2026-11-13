"""Clientes HTTP hacia otros microservicios (Vehiculos, Conductores)."""

from assignments.adapters.outbound.http_clients._shared import UnconfiguredDirectory
from assignments.adapters.outbound.http_clients.drivers_client import HttpDriverDirectory
from assignments.adapters.outbound.http_clients.vehicles_client import HttpVehicleDirectory

__all__ = ["HttpDriverDirectory", "HttpVehicleDirectory", "UnconfiguredDirectory"]
