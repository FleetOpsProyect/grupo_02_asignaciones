"""Pruebas de la entidad Assignment y su maquina de estados."""

from __future__ import annotations

from datetime import date

import pytest

from assignments.domain.assignment import Assignment, AssignmentStatus
from assignments.domain.exceptions import InvalidAssignmentRequestError, InvalidTransitionError


def _make_assignment(start: date = date(2026, 1, 10), end: date = date(2026, 1, 15)) -> Assignment:
    return Assignment.request(
        employee_id="emp-1",
        vehicle_id="veh-1",
        driver_id="drv-1",
        vehicle_type="CAMIONETA",
        start_date=start,
        end_date=end,
    )


def test_request_creates_pending_assignment_with_generated_id() -> None:
    assignment = _make_assignment()

    assert assignment.status == AssignmentStatus.PENDIENTE
    assert assignment.is_active() is True
    assert assignment.origin is None
    assert assignment.destination is None
    assert assignment.id is not None


def test_request_rejects_end_date_not_after_start_date() -> None:
    with pytest.raises(InvalidAssignmentRequestError):
        _make_assignment(start=date(2026, 1, 15), end=date(2026, 1, 10))


def test_request_rejects_equal_start_and_end_date() -> None:
    with pytest.raises(InvalidAssignmentRequestError):
        _make_assignment(start=date(2026, 1, 10), end=date(2026, 1, 10))


def test_full_lifecycle_start_then_finish() -> None:
    assignment = _make_assignment()

    assignment.start()
    status_after_start: AssignmentStatus = assignment.status
    assert status_after_start == AssignmentStatus.EN_CURSO
    assert assignment.is_active() is True

    assignment.finish()
    status_after_finish: AssignmentStatus = assignment.status
    assert status_after_finish == AssignmentStatus.FINALIZADA
    assert assignment.is_active() is False


def test_en_curso_can_be_interrupted_by_incident() -> None:
    assignment = _make_assignment()
    assignment.start()

    assignment.interrupt()

    assert assignment.status == AssignmentStatus.INTERRUMPIDA_POR_INCIDENTE
    assert assignment.is_active() is False


def test_cannot_start_an_assignment_that_is_not_pendiente() -> None:
    assignment = _make_assignment()
    assignment.start()

    with pytest.raises(InvalidTransitionError):
        assignment.start()


def test_cannot_finish_an_assignment_that_is_not_en_curso() -> None:
    assignment = _make_assignment()

    with pytest.raises(InvalidTransitionError):
        assignment.finish()


def test_cannot_interrupt_an_assignment_that_is_not_en_curso() -> None:
    assignment = _make_assignment()

    with pytest.raises(InvalidTransitionError):
        assignment.interrupt()
