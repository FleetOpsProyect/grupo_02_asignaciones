"""Pruebas de logging estructurado."""

from __future__ import annotations

import json
import logging

from assignments.logging_setup import JsonFormatter, configure_logging


def test_json_formatter_includes_exception_when_present() -> None:
    try:
        raise ValueError("invalid value")
    except ValueError:
        record = logging.LogRecord("test", logging.ERROR, __file__, 1, "failed", (), None)
        record.exc_info = __import__("sys").exc_info()

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "ERROR"
    assert payload["message"] == "failed"
    assert "ValueError" in payload["exception"]


def test_configure_logging_replaces_root_handler() -> None:
    configure_logging("debug")

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, JsonFormatter)
