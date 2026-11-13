"""Cliente HTTP al servicio de Vehiculos (otro microservicio de FleetOps).

Implementa VehicleDirectoryPort. Ver `_shared.py` para la nota sobre el
contrato real de la respuesta, que todavia no esta acordado entre los equipos.
"""

from __future__ import annotations

from datetime import date

from assignments.adapters.outbound.http_clients._shared import extract_ids, fetch_json_list


class HttpVehicleDirectory:
    """Consulta GET /vehiculos?estado=ACTIVO&tipo={tipo}&vigencia_hasta={fecha}."""

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def find_active(self, vehicle_type: str, valid_until: date) -> list[str]:
        payload = fetch_json_list(
            f"{self._base_url}/vehiculos",
            params={
                "estado": "ACTIVO",
                "tipo": vehicle_type,
                "vigencia_hasta": valid_until.isoformat(),
            },
            timeout_seconds=self._timeout_seconds,
        )
        return extract_ids(payload)
