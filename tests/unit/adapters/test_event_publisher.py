"""Pruebas del publicador de eventos provisional (solo log, sin broker todavia)."""

from __future__ import annotations

import logging
from datetime import date

import pytest

from assignments.adapters.outbound.messaging import LoggingAssignmentEventPublisher
from assignments.domain.assignment import Assignment


def test_assignment_created_logs_the_event(caplog: pytest.LogCaptureFixture) -> None:
    assignment = Assignment.request(
        employee_id="emp-1",
        vehicle_id="veh-1",
        driver_id="drv-1",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 5),
    )
    publisher = LoggingAssignmentEventPublisher()

    with caplog.at_level(logging.INFO):
        publisher.assignment_created(assignment)

    assert any(record.message == "assignment_created_event" for record in caplog.records)
    record = next(r for r in caplog.records if r.message == "assignment_created_event")
    assert record.assignment_id == str(assignment.id)  # type: ignore[attr-defined]
    assert record.event == "assignment_created_event"  # type: ignore[attr-defined]
