"""Composition root del microservicio: construye create_app() cableando adapters.

Reglas de capas que el equipo debe respetar al llenar domain/ y application/:

- `domain/` y `application/` no importan Flask, SQLAlchemy, redis ni nada de
  `adapters/`. El nucleo de negocio es independiente de la tecnologia.
- Los casos de uso (`application/use_cases/`) reciben sus dependencias por
  constructor, tipadas con los puertos (`typing.Protocol`) definidos en
  `application/ports/`, nunca con las clases concretas de los adapters.
- Solo este modulo (`main.py`) conoce a la vez los adapters concretos y los
  casos de uso: es el unico lugar donde se decide que implementacion concreta
  satisface cada puerto.
"""

from __future__ import annotations

from flask import Flask
from flask_smorest import Api
from prometheus_flask_exporter import PrometheusMetrics

from assignments.adapters.inbound.http.errors import register_error_handlers
from assignments.adapters.inbound.http.health import HealthCheck
from assignments.adapters.inbound.http.health import blp as health_blp
from assignments.adapters.inbound.http.middleware import register_correlation_id
from assignments.adapters.outbound.cache import build_cache_health_check, build_redis_client
from assignments.adapters.outbound.persistence import build_engine
from assignments.adapters.outbound.persistence.health import build_database_health_check
from assignments.config import Settings, get_settings
from assignments.logging_setup import configure_logging


def create_app(
    settings: Settings | None = None,
    readiness_checks: list[HealthCheck] | None = None,
) -> Flask:
    """Construye la aplicacion Flask del microservicio.

    `readiness_checks` permite inyectar verificaciones falsas en las pruebas
    unitarias de /ready. Si se omite, se construyen a partir de la
    configuracion real: PostgreSQL siempre, y Redis solo si REDIS_URL esta
    definido.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    # API REST stateless basada en tokens Bearer (no usa cookies ni sesiones de navegador)
    app = Flask(__name__)  # nosonar
    app.config["API_TITLE"] = settings.app_name
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    if readiness_checks is None:
        engine = build_engine(settings)
        readiness_checks = [build_database_health_check(engine)]
        redis_client = build_redis_client(settings)
        cache_check = build_cache_health_check(redis_client)
        if cache_check is not None:
            readiness_checks.append(cache_check)
    app.config["READINESS_CHECKS"] = readiness_checks

    register_correlation_id(app)

    PrometheusMetrics(app)

    api = Api(app)
    api.register_blueprint(health_blp)

    # Se registra al final: flask-smorest instala su propio manejador de
    # HTTPException al construir Api(app), y Flask usa el ultimo registrado
    # para cada tipo de excepcion. Esto asegura que prevalezca el formato de
    # error estandar de FleetOps sobre el de flask-smorest.
    register_error_handlers(app)

    return app
