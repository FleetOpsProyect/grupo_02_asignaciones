"""Blueprint de asignaciones.

Expone los 4 endpoints de negocio del contrato:

- POST   /assignment           Solicita y crea una asignacion (Proceso 1)
- GET    /assignment/{id}      Consulta una asignacion
- GET    /assignment           Lista paginada, con filtros y resumen por estado
- GET    /assignment/active    Igual que la anterior, restringida a PENDIENTE/EN_CURSO
"""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Any

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields
from werkzeug.exceptions import BadRequest, Conflict, NotFound, ServiceUnavailable

from assignments.application.errors import ExternalServiceUnavailableError
from assignments.application.ports.assignment_repository import AssignmentFilters
from assignments.application.use_cases.create_assignment import (
    CreateAssignmentCommand,
    CreateAssignmentUseCase,
)
from assignments.application.use_cases.get_assignment import GetAssignmentUseCase
from assignments.application.use_cases.list_assignments import (
    AssignmentPage,
    ListAssignmentsUseCase,
)
from assignments.domain.assignment import Assignment, AssignmentStatus
from assignments.domain.exceptions import (
    AssignmentNotFoundError,
    InvalidAssignmentRequestError,
    NoAvailabilityError,
)

blp = Blueprint("assignments", __name__, description="Asignaciones de vehiculo y conductor")

_ACTIVE_STATUSES = frozenset({AssignmentStatus.PENDIENTE, AssignmentStatus.EN_CURSO})
_MAX_PAGE_SIZE = 100


class AssignmentCreateRequestSchema(Schema):
    """Cuerpo de POST /assignment."""

    employee_id = fields.String(required=True)
    vehicle_type = fields.String(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)


class AssignmentResponseSchema(Schema):
    """Representacion de una asignacion en las respuestas."""

    id = fields.UUID(required=True)
    employee_id = fields.String(required=True)
    vehicle_id = fields.String(required=True)
    driver_id = fields.String(required=True)
    vehicle_type = fields.String(required=True)
    status = fields.String(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    origin = fields.String(allow_none=True)
    destination = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)


class AssignmentSummarySchema(Schema):
    """Conteo de asignaciones por estado, para el bloque `resumen`."""

    PENDIENTE = fields.Integer(required=True)
    EN_CURSO = fields.Integer(required=True)
    FINALIZADA = fields.Integer(required=True)
    INTERRUMPIDA_POR_INCIDENTE = fields.Integer(required=True)


class AssignmentListResponseSchema(Schema):
    """Respuesta paginada de GET /assignment y GET /assignment/active."""

    items = fields.List(fields.Nested(AssignmentResponseSchema), required=True)
    page = fields.Integer(required=True)
    size = fields.Integer(required=True)
    total = fields.Integer(required=True)
    resumen = fields.Nested(AssignmentSummarySchema, required=True, attribute="summary")


class AssignmentQueryArgsSchema(Schema):
    """Filtros y paginacion compartidos por GET /assignment y GET /assignment/active."""

    status = fields.String()
    employee_id = fields.String()
    driver_id = fields.String()
    vehicle_id = fields.String()
    start_date = fields.Date()
    end_date = fields.Date()
    page = fields.Integer(load_default=1)
    size = fields.Integer(load_default=20)


def _parse_status_filter(
    status_value: str | None, *, restrict_to_active: bool
) -> AssignmentFilters:
    if status_value is None:
        return AssignmentFilters(statuses=_ACTIVE_STATUSES if restrict_to_active else None)
    try:
        status = AssignmentStatus(status_value)
    except ValueError as error:
        raise BadRequest(f"status invalido: {status_value}") from error
    if restrict_to_active and status not in _ACTIVE_STATUSES:
        raise BadRequest("status debe ser PENDIENTE o EN_CURSO en /assignment/active")
    return AssignmentFilters(statuses=frozenset({status}))


def _parse_list_query(
    args: dict[str, Any], *, restrict_to_active: bool = False
) -> tuple[AssignmentFilters, int, int]:
    page: int = args.get("page", 1)
    size: int = args.get("size", 20)
    if page < 1:
        raise BadRequest("page debe ser mayor o igual a 1")
    if not 1 <= size <= _MAX_PAGE_SIZE:
        raise BadRequest(f"size debe estar entre 1 y {_MAX_PAGE_SIZE}")

    start_date = args.get("start_date")
    end_date = args.get("end_date")
    if start_date is not None and end_date is not None and start_date > end_date:
        raise BadRequest("start_date debe ser anterior o igual a end_date")

    base_filters = _parse_status_filter(args.get("status"), restrict_to_active=restrict_to_active)
    filters = AssignmentFilters(
        statuses=base_filters.statuses,
        employee_id=args.get("employee_id"),
        driver_id=args.get("driver_id"),
        vehicle_id=args.get("vehicle_id"),
        start_date=start_date,
        end_date=end_date,
    )
    return filters, page, size


@blp.route("/assignment")
class AssignmentCollectionResource(MethodView):
    """POST crea una asignacion; GET lista todas, con filtros y resumen por estado."""

    @blp.arguments(AssignmentCreateRequestSchema)  # type: ignore[untyped-decorator]
    @blp.response(HTTPStatus.CREATED, AssignmentResponseSchema)  # type: ignore[untyped-decorator]
    @blp.alt_response(  # type: ignore[untyped-decorator]
        HTTPStatus.BAD_REQUEST, description="Solicitud invalida (p. ej. fechas)"
    )
    @blp.alt_response(  # type: ignore[untyped-decorator]
        HTTPStatus.CONFLICT, description="Sin vehiculo/conductor disponible"
    )
    @blp.alt_response(  # type: ignore[untyped-decorator]
        HTTPStatus.SERVICE_UNAVAILABLE, description="Vehiculos o Conductores no responde"
    )
    def post(self, payload: dict[str, Any]) -> Assignment:
        use_case: CreateAssignmentUseCase = current_app.config["CREATE_ASSIGNMENT_USE_CASE"]
        command = CreateAssignmentCommand(
            employee_id=payload["employee_id"],
            vehicle_type=payload["vehicle_type"],
            start_date=payload["start_date"],
            end_date=payload["end_date"],
        )
        try:
            return use_case.execute(command)
        except InvalidAssignmentRequestError as error:
            raise BadRequest(str(error)) from error
        except NoAvailabilityError as error:
            raise Conflict(str(error)) from error
        except ExternalServiceUnavailableError as error:
            raise ServiceUnavailable(str(error)) from error

    @blp.arguments(AssignmentQueryArgsSchema, location="query")  # type: ignore[untyped-decorator]
    @blp.response(HTTPStatus.OK, AssignmentListResponseSchema)  # type: ignore[untyped-decorator]
    @blp.alt_response(  # type: ignore[untyped-decorator]
        HTTPStatus.BAD_REQUEST, description="Filtros o paginacion invalidos"
    )
    def get(self, args: dict[str, Any]) -> AssignmentPage:
        filters, page, size = _parse_list_query(args)
        use_case: ListAssignmentsUseCase = current_app.config["LIST_ASSIGNMENTS_USE_CASE"]
        return use_case.execute(filters, page, size)


@blp.route("/assignment/active")
class AssignmentActiveResource(MethodView):
    """Lista asignaciones PENDIENTE o EN_CURSO, con los mismos filtros y resumen."""

    @blp.arguments(AssignmentQueryArgsSchema, location="query")  # type: ignore[untyped-decorator]
    @blp.response(HTTPStatus.OK, AssignmentListResponseSchema)  # type: ignore[untyped-decorator]
    @blp.alt_response(  # type: ignore[untyped-decorator]
        HTTPStatus.BAD_REQUEST, description="Filtros o paginacion invalidos"
    )
    def get(self, args: dict[str, Any]) -> AssignmentPage:
        filters, page, size = _parse_list_query(args, restrict_to_active=True)
        use_case: ListAssignmentsUseCase = current_app.config["LIST_ASSIGNMENTS_USE_CASE"]
        return use_case.execute(filters, page, size)


@blp.route("/assignment/<uuid:assignment_id>")
class AssignmentResource(MethodView):
    """Consulta una asignacion por id."""

    @blp.response(HTTPStatus.OK, AssignmentResponseSchema)  # type: ignore[untyped-decorator]
    @blp.alt_response(  # type: ignore[untyped-decorator]
        HTTPStatus.NOT_FOUND, description="No existe una asignacion con ese id"
    )
    def get(self, assignment_id: uuid.UUID) -> Assignment:
        use_case: GetAssignmentUseCase = current_app.config["GET_ASSIGNMENT_USE_CASE"]
        try:
            return use_case.execute(assignment_id)
        except AssignmentNotFoundError as error:
            raise NotFound(str(error)) from error
