"""Pruebas de ListAssignmentsUseCase."""

from __future__ import annotations

from datetime import date

from assignments.application.ports.assignment_repository import AssignmentFilters
from assignments.application.use_cases.list_assignments import ListAssignmentsUseCase
from assignments.domain.assignment import Assignment, AssignmentStatus
from tests.unit.application.fakes import FakeAssignmentRepository


def _assignment(employee_id: str, status: AssignmentStatus) -> Assignment:
    assignment = Assignment.request(
        employee_id=employee_id,
        vehicle_id="veh-1",
        driver_id="drv-1",
        vehicle_type="CAMIONETA",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 5),
    )
    assignment.status = status
    return assignment


def test_paginates_and_summarizes_by_status() -> None:
    assignments = [
        _assignment("emp-1", AssignmentStatus.PENDIENTE),
        _assignment("emp-1", AssignmentStatus.EN_CURSO),
        _assignment("emp-1", AssignmentStatus.FINALIZADA),
        _assignment("emp-2", AssignmentStatus.PENDIENTE),
    ]
    use_case = ListAssignmentsUseCase(FakeAssignmentRepository(assignments))

    page = use_case.execute(AssignmentFilters(employee_id="emp-1"), page=1, size=2)

    assert page.total == 3
    assert len(page.items) == 2
    assert page.summary[AssignmentStatus.PENDIENTE] == 1
    assert page.summary[AssignmentStatus.EN_CURSO] == 1
    assert page.summary[AssignmentStatus.FINALIZADA] == 1
    assert page.summary[AssignmentStatus.INTERRUMPIDA_POR_INCIDENTE] == 0


def test_filters_by_statuses_set_for_active_only() -> None:
    assignments = [
        _assignment("emp-1", AssignmentStatus.PENDIENTE),
        _assignment("emp-1", AssignmentStatus.EN_CURSO),
        _assignment("emp-1", AssignmentStatus.FINALIZADA),
    ]
    use_case = ListAssignmentsUseCase(FakeAssignmentRepository(assignments))
    active_filters = AssignmentFilters(
        statuses=frozenset({AssignmentStatus.PENDIENTE, AssignmentStatus.EN_CURSO})
    )

    page = use_case.execute(active_filters, page=1, size=10)

    assert page.total == 2
    assert {a.status for a in page.items} == {
        AssignmentStatus.PENDIENTE,
        AssignmentStatus.EN_CURSO,
    }
