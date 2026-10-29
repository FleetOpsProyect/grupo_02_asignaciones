"""Blueprint de salud: /health y /ready, documentados en Swagger."""

from __future__ import annotations

from typing import Protocol

from flask import Response, current_app, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

blp = Blueprint("health", __name__, description="Salud y disponibilidad del servicio")


class HealthCheck(Protocol):
    """Verificacion minima que debe cumplir una dependencia para participar en /ready."""

    name: str

    def __call__(self) -> bool: ...


class HealthSchema(Schema):
    status = fields.String(required=True)
    service = fields.String(required=True)


class ReadinessSchema(Schema):
    status = fields.String(required=True)
    dependencies = fields.Dict(keys=fields.String(), values=fields.Boolean(), required=True)


@blp.route("/health")
class HealthResource(MethodView):
    """Indica que el proceso esta vivo; no consulta ninguna dependencia."""

    @blp.response(200, HealthSchema)  # type: ignore[untyped-decorator]
    def get(self) -> dict[str, str]:
        service_name: str = current_app.config["SERVICE_NAME"]
        return {"status": "UP", "service": service_name}


@blp.route("/ready")
class ReadinessResource(MethodView):
    """Verifica cada dependencia inyectada en create_app(); 503 si alguna falla."""

    @blp.doc(  # type: ignore[untyped-decorator]
        responses={
            200: {"description": "Todas las dependencias configuradas responden"},
            503: {"description": "Al menos una dependencia no responde"},
        }
    )
    def get(self) -> tuple[Response, int]:
        checks: list[HealthCheck] = current_app.config["READINESS_CHECKS"]
        dependencies = {check.name: check() for check in checks}
        healthy = all(dependencies.values())
        body = {"status": "UP" if healthy else "DOWN", "dependencies": dependencies}
        return jsonify(body), (200 if healthy else 503)
