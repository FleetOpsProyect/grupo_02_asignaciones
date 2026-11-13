"""Pruebas de integracion de SqlAlchemyAssignmentRepository contra PostgreSQL real."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.community.postgres import PostgresContainer

from assignments.adapters.outbound.persistence import Base, SqlAlchemyAssignmentRepository
from assignments.adapters.outbound.persistence.engine import build_engine, build_session_factory
from assignments.application.ports.assignment_repository import AssignmentFilters
from assignments.config import Settings
from assignments.domain.assignment import Assignment, AssignmentStatus

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def session_factory() -> Iterator[sessionmaker[Session]]:
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        settings = Settings(database_url=postgres.get_connection_url())
        engine = build_engine(settings)
        Base.metadata.create_all(engine)
        yield build_session_factory(engine)


@pytest.fixture
def repository(
    session_factory: sessionmaker[Session],
) -> SqlAlchemyAssignmentRepository:
    with session_factory() as session:
        session.query(Base.metadata.tables["assignments"]).delete()
        session.commit()
    return SqlAlchemyAssignmentRepository(session_factory)


def _assignment(
    employee_id: str = "emp-1",
    vehicle_id: str = "veh-1",
    driver_id: str = "drv-1",
    status: AssignmentStatus = AssignmentStatus.PENDIENTE,
    start: date = date(2026, 3, 1),
    end: date = date(2026, 3, 5),
) -> Assignment:
    assignment = Assignment.request(
        employee_id=employee_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        vehicle_type="CAMIONETA",
        start_date=start,
        end_date=end,
    )
    assignment.status = status
    return assignment


def test_add_and_get_by_id_round_trip(repository: SqlAlchemyAssignmentRepository) -> None:
    assignment = _assignment()

    repository.add(assignment)
    found = repository.get_by_id(assignment.id)

    assert found is not None
    assert found.id == assignment.id
    assert found.employee_id == assignment.employee_id
    assert found.status == AssignmentStatus.PENDIENTE
    assert found.origin is None


def test_get_by_id_returns_none_when_missing(repository: SqlAlchemyAssignmentRepository) -> None:
    assert repository.get_by_id(_assignment().id) is None


def test_search_filters_by_employee_and_paginates(
    repository: SqlAlchemyAssignmentRepository,
) -> None:
    for i in range(3):
        repository.add(_assignment(employee_id="emp-1", vehicle_id=f"veh-{i}"))
    repository.add(_assignment(employee_id="emp-2"))

    items, total = repository.search(AssignmentFilters(employee_id="emp-1"), page=1, size=2)

    assert total == 3
    assert len(items) == 2
    assert all(item.employee_id == "emp-1" for item in items)


def test_count_by_status_ignores_the_status_filter(
    repository: SqlAlchemyAssignmentRepository,
) -> None:
    repository.add(_assignment(status=AssignmentStatus.PENDIENTE))
    repository.add(_assignment(status=AssignmentStatus.EN_CURSO))
    repository.add(_assignment(status=AssignmentStatus.FINALIZADA))

    summary = repository.count_by_status(
        AssignmentFilters(statuses=frozenset({AssignmentStatus.PENDIENTE}))
    )

    assert summary[AssignmentStatus.PENDIENTE] == 1
    assert summary[AssignmentStatus.EN_CURSO] == 1
    assert summary[AssignmentStatus.FINALIZADA] == 1
    assert summary[AssignmentStatus.INTERRUMPIDA_POR_INCIDENTE] == 0


def test_busy_vehicle_ids_only_counts_overlapping_active_assignments(
    repository: SqlAlchemyAssignmentRepository,
) -> None:
    repository.add(
        _assignment(vehicle_id="veh-busy", start=date(2026, 3, 3), end=date(2026, 3, 10))
    )
    repository.add(
        _assignment(
            vehicle_id="veh-finished",
            status=AssignmentStatus.FINALIZADA,
            start=date(2026, 3, 3),
            end=date(2026, 3, 10),
        )
    )
    repository.add(_assignment(vehicle_id="veh-free", start=date(2026, 4, 1), end=date(2026, 4, 5)))

    busy = repository.busy_vehicle_ids(
        ["veh-busy", "veh-finished", "veh-free"], date(2026, 3, 1), date(2026, 3, 5)
    )

    assert busy == {"veh-busy"}
