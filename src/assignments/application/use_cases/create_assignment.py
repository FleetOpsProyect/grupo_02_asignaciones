"""Caso de uso: solicitar y crear una asignacion (Proceso 1 del caso de estudio)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from assignments.application.ports.assignment_repository import AssignmentRepository
from assignments.application.ports.event_publisher import AssignmentEventPublisher
from assignments.application.ports.fleet_directory import DriverDirectoryPort, VehicleDirectoryPort
from assignments.domain.assignment import Assignment
from assignments.domain.exceptions import InvalidAssignmentRequestError, NoAvailabilityError


@dataclass(frozen=True)
class CreateAssignmentCommand:
    """Datos de la solicitud de asignacion hecha por un empleado."""

    employee_id: str
    vehicle_type: str
    start_date: date
    end_date: date


class CreateAssignmentUseCase:
    """Busca un vehiculo y un conductor activos, vigentes y libres, y crea la asignacion.

    Un vehiculo/conductor es apto si el directorio correspondiente lo reporta
    ACTIVO y vigente hasta `end_date`, y esta libre si no tiene otra
    asignacion PENDIENTE o EN_CURSO que se cruce con el periodo solicitado.
    """

    def __init__(
        self,
        repository: AssignmentRepository,
        vehicle_directory: VehicleDirectoryPort,
        driver_directory: DriverDirectoryPort,
        event_publisher: AssignmentEventPublisher,
    ) -> None:
        self._repository = repository
        self._vehicle_directory = vehicle_directory
        self._driver_directory = driver_directory
        self._event_publisher = event_publisher

    def execute(self, command: CreateAssignmentCommand) -> Assignment:
        if command.end_date <= command.start_date:
            # Se valida aqui, antes de consultar disponibilidad: si no, una
            # fecha invertida puede "casar" por coincidencia con una
            # asignacion existente y salir como 409 en vez de 400.
            raise InvalidAssignmentRequestError("end_date debe ser posterior a start_date")

        candidate_vehicle_ids = self._vehicle_directory.find_active(
            command.vehicle_type, command.end_date
        )
        candidate_driver_ids = self._driver_directory.find_active(command.end_date)
        if not candidate_vehicle_ids or not candidate_driver_ids:
            raise NoAvailabilityError(
                "No hay vehiculo y conductor activos y vigentes para el periodo solicitado"
            )

        busy_vehicle_ids = self._repository.busy_vehicle_ids(
            candidate_vehicle_ids, command.start_date, command.end_date
        )
        busy_driver_ids = self._repository.busy_driver_ids(
            candidate_driver_ids, command.start_date, command.end_date
        )

        vehicle_id = next((v for v in candidate_vehicle_ids if v not in busy_vehicle_ids), None)
        driver_id = next((d for d in candidate_driver_ids if d not in busy_driver_ids), None)
        if vehicle_id is None or driver_id is None:
            raise NoAvailabilityError(
                "El vehiculo y el conductor aptos ya tienen otra asignacion en esas fechas"
            )

        assignment = Assignment.request(
            employee_id=command.employee_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            vehicle_type=command.vehicle_type,
            start_date=command.start_date,
            end_date=command.end_date,
        )
        self._repository.add(assignment)
        self._event_publisher.assignment_created(assignment)
        return assignment
