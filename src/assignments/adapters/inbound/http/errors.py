"""Formato de error estandar de FleetOps para cualquier error HTTP (404, 500, ...)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException

from assignments.correlation import get_correlation_id

logger = logging.getLogger(__name__)

_ERROR_CODES: dict[int, str] = {
    400: "SOLICITUD_INVALIDA",
    401: "NO_AUTENTICADO",
    403: "NO_AUTORIZADO",
    404: "RECURSO_NO_ENCONTRADO",
    405: "METODO_NO_PERMITIDO",
    409: "CONFLICTO",
    422: "ENTIDAD_NO_PROCESABLE",
    429: "DEMASIADAS_SOLICITUDES",
    500: "ERROR_INTERNO",
    503: "SERVICIO_NO_DISPONIBLE",
}


def _error_code(status_code: int) -> str:
    if status_code in _ERROR_CODES:
        return _ERROR_CODES[status_code]
    try:
        return HTTPStatus(status_code).phrase.upper().replace(" ", "_")
    except ValueError:
        return "ERROR_INTERNO"


def _build_body(status_code: int, message: str) -> dict[str, Any]:
    return {
        "codigo": _error_code(status_code),
        "mensaje": message,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ruta": request.path,
        "correlation_id": get_correlation_id() or "",
    }


def register_error_handlers(app: Flask) -> None:
    """Registra los manejadores que traducen cualquier error a el formato estandar."""

    @app.errorhandler(HTTPException)
    def _handle_http_exception(error: HTTPException) -> tuple[Response, int]:
        status_code = error.code or 500
        message = error.description or error.name or "Error"
        response = jsonify(_build_body(status_code, message))
        return response, status_code

    @app.errorhandler(Exception)
    def _handle_unexpected_exception(error: Exception) -> tuple[Response, int]:
        logger.exception("Error no controlado", exc_info=error)
        response = jsonify(_build_body(500, "Ha ocurrido un error inesperado"))
        return response, 500
