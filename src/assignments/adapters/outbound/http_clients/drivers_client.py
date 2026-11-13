"""Cliente HTTP al servicio de Conductores (otro microservicio de FleetOps).

Implementa DriverDirectoryPort. Ver `_shared.py` para la nota sobre el
contrato real de la respuesta, que todavia no esta acordado entre los equipos.
"""

from __future__ import annotations

from datetime import date

from assignments.adapters.outbound.http_clients._shared import extract_ids, fetch_json_list


class HttpDriverDirectory:
    """Consulta GET /conductores?estado=ACTIVO&vigencia_hasta={fecha}."""

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def find_active(self, valid_until: date) -> list[str]:
        payload = fetch_json_list(
            f"{self._base_url}/conductores",
            params={"estado": "ACTIVO", "vigencia_hasta": valid_until.isoformat()},
            timeout_seconds=self._timeout_seconds,
        )
        return extract_ids(payload)
