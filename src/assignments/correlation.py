"""Correlation id compartido entre el middleware HTTP y el logging estructurado."""

from __future__ import annotations

import contextvars
import uuid

CORRELATION_ID_HEADER = "X-Correlation-Id"

_correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def generate_correlation_id() -> str:
    """Genera un nuevo correlation id."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Asocia el correlation id a la peticion/hilo actual."""
    _correlation_id_var.set(correlation_id)


def get_correlation_id() -> str | None:
    """Obtiene el correlation id de la peticion/hilo actual, si existe."""
    return _correlation_id_var.get()
