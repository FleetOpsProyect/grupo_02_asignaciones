"""Pruebas end-to-end (via Flask test client) de los 4 endpoints de /assignment.

Usan los casos de uso reales con un repositorio y directorios en memoria
(los mismos dobles de tests/unit/application/fakes.py), para probar el
cableado HTTP real (schemas, status codes, mapeo de errores) sin necesitar
Postgres ni los servicios de Vehiculos/Conductores.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import pytest
from flask import Flask
from flask.testing import FlaskClient

from assignments.application.use_cases.create_assignment import CreateAssignmentUseCase
from assignments.application.use_cases.get_assignment import GetAssignmentUseCase
from assignments.application.use_cases.list_assignments import ListAssignmentsUseCase
from assignments.domain.assignment import Assignment, AssignmentStatus
from tests.unit.application.fakes import (
    FakeAssignmentRepository,
    FakeDriverDirectory,
    FakeEventPublisher,
    FakeVehicleDirectory,
)
from tests.unit.fakes import FakeHealthCheck


@pytest.fixture
def repository() -> FakeAssignmentRepository:
    return FakeAssignmentRepository()


@pytest.fixture
def build_client(
    make_app: Callable[[list[FakeHealthCheck]], Flask],
    repository: FakeAssignmentRepository,
) -> Callable[..., FlaskClient]:
    def _build(
        vehicle_ids: list[str] | None = None,
        driver_ids: list[str] | None = None,
        vehicles_unavailable: bool = False,
        drivers_unavailable: bool = False,
    ) -> FlaskClient:
        app = make_app([FakeHealthCheck("database", True)])
        app.config["CREATE_ASSIGNMENT_USE_CASE"] = CreateAssignmentUseCase(
            repository=repository,
            vehicle_directory=FakeVehicleDirectory(
                vehicle_ids if vehicle_ids is not None else ["veh-1"],
                unavailable=vehicles_unavailable,
            ),
            driver_directory=FakeDriverDirectory(
                driver_ids if driver_ids is not None else ["drv-1"],
                unavailable=drivers_unavailable,
            ),
            event_publisher=FakeEventPublisher(),
        )
        app.config["GET_ASSIGNMENT_USE_CASE"] = GetAssignmentUseCase(repository)
        app.config["LIST_ASSIGNMENTS_USE_CASE"] = ListAssignmentsUseCase(repository)
        return app.test_client()

    return _build


_CREATE_PAYLOAD = {
    "employee_id": "emp-1",
    "vehicle_type": "CAMIONETA",
    "start_date": "2026-03-01",
    "end_date": "2026-03-05",
}


def test_post_assignment_creates_a_pending_assignment(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client()

    response = client.post("/assignment", json=_CREATE_PAYLOAD)

    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "PENDIENTE"
    assert body["employee_id"] == "emp-1"
    assert body["vehicle_id"] == "veh-1"
    assert body["driver_id"] == "drv-1"
    assert body["origin"] is None


def test_post_assignment_rejects_end_date_not_after_start_date(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client()

    invalid_payload = {**_CREATE_PAYLOAD, "start_date": "2026-03-05", "end_date": "2026-03-01"}
    response = client.post("/assignment", json=invalid_payload)

    assert response.status_code == 400


def test_post_assignment_returns_409_when_no_vehicle_is_available(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client(vehicle_ids=[])

    response = client.post("/assignment", json=_CREATE_PAYLOAD)

    assert response.status_code == 409


def test_post_assignment_returns_503_when_vehicle_service_is_unreachable(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client(vehicles_unavailable=True)

    response = client.post("/assignment", json=_CREATE_PAYLOAD)

    assert response.status_code == 503


def test_get_assignment_by_id_returns_200(
    build_client: Callable[..., FlaskClient], repository: FakeAssignmentRepository
) -> None:
    client = build_client()
    created = client.post("/assignment", json=_CREATE_PAYLOAD).get_json()

    response = client.get(f"/assignment/{created['id']}")

    assert response.status_code == 200
    assert response.get_json()["id"] == created["id"]


def test_get_assignment_by_id_returns_404_when_missing(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client()

    response = client.get("/assignment/11111111-1111-1111-1111-111111111111")

    assert response.status_code == 404


def test_get_assignment_list_paginates_and_summarizes(
    build_client: Callable[..., FlaskClient], repository: FakeAssignmentRepository
) -> None:
    client = build_client()
    for i in range(3):
        repository.add(
            Assignment.request(
                employee_id="emp-1",
                vehicle_id=f"veh-{i}",
                driver_id="drv-1",
                vehicle_type="CAMIONETA",
                start_date=date(2026, 3, 1),
                end_date=date(2026, 3, 5),
            )
        )

    response = client.get("/assignment?employee_id=emp-1&page=1&size=2")

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["resumen"]["PENDIENTE"] == 3


def test_get_assignment_list_rejects_invalid_status(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client()

    response = client.get("/assignment?status=NO_EXISTE")

    assert response.status_code == 400


def test_get_assignment_list_rejects_page_less_than_one(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client()

    response = client.get("/assignment?page=0")

    assert response.status_code == 400


def test_get_active_assignments_only_returns_pendiente_and_en_curso(
    build_client: Callable[..., FlaskClient], repository: FakeAssignmentRepository
) -> None:
    client = build_client()
    pendiente = Assignment.request(
        employee_id="emp-1",
        vehicle_id="veh-1",
        driver_id="drv-1",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 5),
    )
    finalizada = Assignment.request(
        employee_id="emp-1",
        vehicle_id="veh-2",
        driver_id="drv-2",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 5),
    )
    finalizada.status = AssignmentStatus.FINALIZADA
    repository.add(pendiente)
    repository.add(finalizada)

    response = client.get("/assignment/active")

    assert response.status_code == 200
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "PENDIENTE"


def test_get_active_assignments_rejects_a_non_active_status_filter(
    build_client: Callable[..., FlaskClient],
) -> None:
    client = build_client()

    response = client.get("/assignment/active?status=FINALIZADA")

    assert response.status_code == 400
