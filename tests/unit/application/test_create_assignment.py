"""Pruebas de CreateAssignmentUseCase."""

from __future__ import annotations

from datetime import date

import pytest

from assignments.application.errors import ExternalServiceUnavailableError
from assignments.application.use_cases.create_assignment import (
    CreateAssignmentCommand,
    CreateAssignmentUseCase,
)
from assignments.domain.assignment import Assignment, AssignmentStatus
from assignments.domain.exceptions import InvalidAssignmentRequestError, NoAvailabilityError
from tests.unit.application.fakes import (
    FakeAssignmentRepository,
    FakeDriverDirectory,
    FakeEventPublisher,
    FakeVehicleDirectory,
)

_COMMAND = CreateAssignmentCommand(
    employee_id="emp-1",
    vehicle_type="CAMIONETA",
    start_date=date(2026, 2, 1),
    end_date=date(2026, 2, 5),
)


def _build_use_case(
    repository: FakeAssignmentRepository | None = None,
    vehicle_directory: FakeVehicleDirectory | None = None,
    driver_directory: FakeDriverDirectory | None = None,
    event_publisher: FakeEventPublisher | None = None,
) -> tuple[CreateAssignmentUseCase, FakeEventPublisher]:
    publisher = event_publisher or FakeEventPublisher()
    use_case = CreateAssignmentUseCase(
        repository=repository or FakeAssignmentRepository(),
        vehicle_directory=vehicle_directory or FakeVehicleDirectory(["veh-1"]),
        driver_directory=driver_directory or FakeDriverDirectory(["drv-1"]),
        event_publisher=publisher,
    )
    return use_case, publisher


def test_creates_pending_assignment_with_first_available_candidates() -> None:
    use_case, publisher = _build_use_case(
        vehicle_directory=FakeVehicleDirectory(["veh-1", "veh-2"]),
        driver_directory=FakeDriverDirectory(["drv-1", "drv-2"]),
    )

    assignment = use_case.execute(_COMMAND)

    assert assignment.status == AssignmentStatus.PENDIENTE
    assert assignment.vehicle_id == "veh-1"
    assert assignment.driver_id == "drv-1"
    assert publisher.published == [assignment]


def test_raises_no_availability_when_no_vehicles_are_active() -> None:
    use_case, _ = _build_use_case(vehicle_directory=FakeVehicleDirectory([]))

    with pytest.raises(NoAvailabilityError):
        use_case.execute(_COMMAND)


def test_raises_no_availability_when_no_drivers_are_active() -> None:
    use_case, _ = _build_use_case(driver_directory=FakeDriverDirectory([]))

    with pytest.raises(NoAvailabilityError):
        use_case.execute(_COMMAND)


def test_skips_vehicle_already_assigned_in_overlapping_dates() -> None:
    existing = Assignment.request(
        employee_id="emp-0",
        vehicle_id="veh-1",
        driver_id="drv-other",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 2, 3),
        end_date=date(2026, 2, 10),
    )
    use_case, _ = _build_use_case(
        repository=FakeAssignmentRepository([existing]),
        vehicle_directory=FakeVehicleDirectory(["veh-1", "veh-2"]),
        driver_directory=FakeDriverDirectory(["drv-1"]),
    )

    assignment = use_case.execute(_COMMAND)

    assert assignment.vehicle_id == "veh-2"


def test_raises_no_availability_when_every_candidate_is_busy() -> None:
    existing = Assignment.request(
        employee_id="emp-0",
        vehicle_id="veh-1",
        driver_id="drv-1",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 2, 3),
        end_date=date(2026, 2, 10),
    )
    use_case, _ = _build_use_case(repository=FakeAssignmentRepository([existing]))

    with pytest.raises(NoAvailabilityError):
        use_case.execute(_COMMAND)


def test_rejects_end_date_not_after_start_date_before_checking_availability() -> None:
    """Regresion: una fecha invertida no debe "colarse" como 409 por coincidir
    por casualidad con una asignacion existente; debe fallar como 400 antes
    de llegar a consultar disponibilidad."""
    existing = Assignment.request(
        employee_id="emp-0",
        vehicle_id="veh-1",
        driver_id="drv-1",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 5),
    )
    use_case, _ = _build_use_case(repository=FakeAssignmentRepository([existing]))
    reversed_command = CreateAssignmentCommand(
        employee_id="emp-1",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 2, 5),
        end_date=date(2026, 2, 1),
    )

    with pytest.raises(InvalidAssignmentRequestError):
        use_case.execute(reversed_command)


def test_propagates_external_service_unavailable_from_vehicle_directory() -> None:
    use_case, _ = _build_use_case(vehicle_directory=FakeVehicleDirectory(unavailable=True))

    with pytest.raises(ExternalServiceUnavailableError):
        use_case.execute(_COMMAND)
