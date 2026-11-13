"""Puertos hacia los servicios de Vehiculos y Conductores (otros microservicios de FleetOps).

Se consumen por HTTP. El contrato exacto de esos servicios (campos, paginacion,
nombres de parametros) todavia no esta acordado con los otros grupos, asi que
estos puertos solo definen lo minimo que `application/` necesita: una lista de
ids de candidatos activos y vigentes. El adapter concreto (outbound/http_clients)
se ajustara cuando se conozca el contrato real.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol


class VehicleDirectoryPort(Protocol):
    """Puerto hacia el servicio de Vehiculos."""

    def find_active(self, vehicle_type: str, valid_until: date) -> list[str]:
        """Ids de vehiculos ACTIVOS, del tipo pedido, con vigencia hasta `valid_until`."""
        ...


class DriverDirectoryPort(Protocol):
    """Puerto hacia el servicio de Conductores."""

    def find_active(self, valid_until: date) -> list[str]:
        """Ids de conductores ACTIVOS, con vigencia hasta `valid_until`."""
        ...
