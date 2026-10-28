"""Dobles de prueba usados por las pruebas unitarias."""

from __future__ import annotations


class FakeHealthCheck:
    """Verificacion de dependencia falsa, controlada por la prueba."""

    def __init__(self, name: str, healthy: bool) -> None:
        self.name = name
        self._healthy = healthy

    def __call__(self) -> bool:
        return self._healthy
