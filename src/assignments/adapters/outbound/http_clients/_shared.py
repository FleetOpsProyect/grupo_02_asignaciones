"""Helper interno compartido por los clientes HTTP a Vehiculos y Conductores.

El contrato real de esas respuestas (forma exacta del JSON, paginacion,
nombres de campos) todavia no esta acordado con los equipos que las
desarrollan. Se asume, segun el documento de contexto del curso, que cada
servicio devuelve un arreglo JSON de objetos con al menos un campo "id".
Ajustar `extract_ids` cuando se conozca el contrato real de cada servicio.
"""

from __future__ import annotations

import requests

from assignments.application.errors import ExternalServiceUnavailableError


def fetch_json_list(
    url: str, params: dict[str, str], timeout_seconds: float
) -> list[dict[str, object]]:
    """Hace un GET y devuelve el cuerpo como lista de objetos JSON.

    Traduce cualquier falla de red, timeout o respuesta no-2xx a
    ExternalServiceUnavailableError, que la capa de aplicacion mapea a 503.
    """
    try:
        response = requests.get(url, params=params, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as error:
        raise ExternalServiceUnavailableError(f"{url} no respondio") from error

    payload = response.json()
    if not isinstance(payload, list):
        raise ExternalServiceUnavailableError(
            f"Respuesta inesperada de {url}: se esperaba un arreglo JSON"
        )
    return payload


def extract_ids(payload: list[dict[str, object]]) -> list[str]:
    """Extrae el campo "id" de cada objeto de la respuesta."""
    return [str(item["id"]) for item in payload if "id" in item]


class UnconfiguredDirectory:
    """Placeholder cuando la URL del servicio externo no esta configurada.

    Cualquier llamada falla con ExternalServiceUnavailableError (503), igual
    que si el servicio real estuviera caido. `main.py` lo usa en vez de
    HttpVehicleDirectory/HttpDriverDirectory mientras no se conecte un
    ambiente real de Vehiculos/Conductores.
    """

    def __init__(self, service_name: str) -> None:
        self._service_name = service_name

    def find_active(self, *args: object, **kwargs: object) -> list[str]:
        raise ExternalServiceUnavailableError(
            f"{self._service_name} no esta configurado (falta su URL)"
        )
