"""Unit tests for structured logging helpers."""

from __future__ import annotations

import io
import json
import logging

from dce.infrastructure.logging import (
    JsonLogFormatter,
    configure_logging,
    reset_logging_for_tests,
    resolve_log_format,
    resolve_log_level,
)


def setup_function() -> None:
    reset_logging_for_tests()


def teardown_function() -> None:
    reset_logging_for_tests()


def test_resolve_level_and_format() -> None:
    assert resolve_log_level(verbose=True) == logging.DEBUG
    assert resolve_log_level(verbose=False) == logging.WARNING
    assert resolve_log_level(level="INFO") == logging.INFO
    assert resolve_log_level(environ={"DCE_LOG_LEVEL": "ERROR"}) == logging.ERROR
    assert resolve_log_format(log_format="json") == "json"
    assert resolve_log_format(environ={"DCE_LOG_FORMAT": "JSON"}) == "json"
    assert resolve_log_format() == "text"


def test_json_formatter_emits_object() -> None:
    record = logging.LogRecord(
        name="dce.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    record.workspace = "demo"  # type: ignore[attr-defined]
    line = JsonLogFormatter().format(record)
    payload = json.loads(line)
    assert payload["msg"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "dce.test"
    assert payload["workspace"] == "demo"


def test_configure_logging_json_to_stream() -> None:
    stream = io.StringIO()
    configure_logging(level=logging.INFO, log_format="json", stream=stream, force=True)
    logging.getLogger("dce.sample").info("indexed %s", 3)
    line = stream.getvalue().strip()
    payload = json.loads(line)
    assert payload["msg"] == "indexed 3"
    assert payload["logger"] == "dce.sample"
