"""Pruebas de los clientes HTTP a Vehiculos y Conductores."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
import requests

from assignments.adapters.outbound.http_clients import UnconfiguredDirectory
from assignments.adapters.outbound.http_clients.drivers_client import HttpDriverDirectory
from assignments.adapters.outbound.http_clients.vehicles_client import HttpVehicleDirectory
from assignments.application.errors import ExternalServiceUnavailableError


class _FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self) -> Any:
        return self._payload


def test_vehicle_directory_extracts_ids_from_a_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_get(url: str, params: dict[str, str], timeout: float) -> _FakeResponse:
        captured["url"] = url
        captured["params"] = params
        return _FakeResponse([{"id": "veh-1"}, {"id": "veh-2"}])

    monkeypatch.setattr(requests, "get", fake_get)
    directory = HttpVehicleDirectory("http://vehiculos.local", timeout_seconds=1.0)

    ids = directory.find_active("CAMIONETA", date(2026, 3, 1))

    assert ids == ["veh-1", "veh-2"]
    assert captured["url"] == "http://vehiculos.local/vehiculos"
    assert captured["params"] == {
        "estado": "ACTIVO",
        "tipo": "CAMIONETA",
        "vigencia_hasta": "2026-03-01",
    }


def test_driver_directory_extracts_ids_from_a_successful_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse([{"id": "drv-1"}]))
    directory = HttpDriverDirectory("http://conductores.local", timeout_seconds=1.0)

    ids = directory.find_active(date(2026, 3, 1))

    assert ids == ["drv-1"]


def test_vehicle_directory_raises_when_the_request_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(*args: object, **kwargs: object) -> _FakeResponse:
        raise requests.ConnectionError("no se pudo conectar")

    monkeypatch.setattr(requests, "get", fake_get)
    directory = HttpVehicleDirectory("http://vehiculos.local", timeout_seconds=1.0)

    with pytest.raises(ExternalServiceUnavailableError):
        directory.find_active("CAMIONETA", date(2026, 3, 1))


def test_vehicle_directory_raises_when_the_response_is_not_2xx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse([], status_code=500))
    directory = HttpVehicleDirectory("http://vehiculos.local", timeout_seconds=1.0)

    with pytest.raises(ExternalServiceUnavailableError):
        directory.find_active("CAMIONETA", date(2026, 3, 1))


def test_vehicle_directory_raises_when_the_payload_is_not_a_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse({"items": []}))
    directory = HttpVehicleDirectory("http://vehiculos.local", timeout_seconds=1.0)

    with pytest.raises(ExternalServiceUnavailableError):
        directory.find_active("CAMIONETA", date(2026, 3, 1))


def test_unconfigured_directory_always_raises() -> None:
    directory = UnconfiguredDirectory("Vehiculos")

    with pytest.raises(ExternalServiceUnavailableError):
        directory.find_active("CAMIONETA", date(2026, 3, 1))
