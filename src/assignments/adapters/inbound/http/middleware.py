"""Middleware HTTP que propaga el correlation id entre peticion, respuesta y logs."""

from __future__ import annotations

from flask import Flask, Response, g, request

from assignments.correlation import (
    CORRELATION_ID_HEADER,
    generate_correlation_id,
    set_correlation_id,
)


def register_correlation_id(app: Flask) -> None:
    """Lee X-Correlation-Id de la peticion (o genera uno) y lo devuelve en la respuesta."""

    @app.before_request
    def _assign_correlation_id() -> None:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or generate_correlation_id()
        g.correlation_id = correlation_id
        set_correlation_id(correlation_id)

    @app.after_request
    def _echo_correlation_id(response: Response) -> Response:
        response.headers[CORRELATION_ID_HEADER] = g.get("correlation_id", "")
        return response
