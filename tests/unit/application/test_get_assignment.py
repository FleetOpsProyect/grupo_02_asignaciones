"""Pruebas de GetAssignmentUseCase."""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from assignments.application.use_cases.get_assignment import GetAssignmentUseCase
from assignments.domain.assignment import Assignment
from assignments.domain.exceptions import AssignmentNotFoundError
from tests.unit.application.fakes import FakeAssignmentRepository


def test_returns_the_assignment_when_it_exists() -> None:
    assignment = Assignment.request(
        employee_id="emp-1",
        vehicle_id="veh-1",
        driver_id="drv-1",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 5),
    )
    use_case = GetAssignmentUseCase(FakeAssignmentRepository([assignment]))

    result = use_case.execute(assignment.id)

    assert result is assignment


def test_raises_not_found_when_the_assignment_does_not_exist() -> None:
    use_case = GetAssignmentUseCase(FakeAssignmentRepository([]))

    with pytest.raises(AssignmentNotFoundError):
        use_case.execute(uuid.uuid4())
