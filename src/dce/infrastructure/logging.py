"""Minimal structured logging for DCE (stdlib only)."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any, Literal, TextIO

LogFormat = Literal["text", "json"]

_CONFIGURED = False


class JsonLogFormatter(logging.Formatter):
    """Emit one JSON object per log record (JSON Lines)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "taskName",
            }:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except (TypeError, ValueError):
                payload[key] = repr(value)
        return json.dumps(payload, ensure_ascii=False)


def resolve_log_level(
    *,
    verbose: bool = False,
    level: str | None = None,
    environ: dict[str, str] | None = None,
) -> int:
    """Resolve logging level from explicit value, env, or verbose flag."""
    env = environ if environ is not None else os.environ
    raw = (level or env.get("DCE_LOG_LEVEL") or "").strip().upper()
    if raw:
        return getattr(logging, raw, logging.INFO)
    if verbose:
        return logging.DEBUG
    return logging.WARNING


def resolve_log_format(
    *,
    log_format: str | None = None,
    environ: dict[str, str] | None = None,
) -> LogFormat:
    """Resolve log format from option or ``DCE_LOG_FORMAT`` (default text)."""
    env = environ if environ is not None else os.environ
    raw = (log_format or env.get("DCE_LOG_FORMAT") or "text").strip().lower()
    if raw == "json":
        return "json"
    return "text"


def configure_logging(
    *,
    level: int | None = None,
    log_format: LogFormat | None = None,
    verbose: bool = False,
    stream: TextIO | None = None,
    force: bool = False,
) -> None:
    """Configure the root ``dce`` logger hierarchy to write to stderr.

    Safe to call multiple times; subsequent calls are no-ops unless ``force``.
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    resolved_level = level if level is not None else resolve_log_level(verbose=verbose)
    resolved_format = log_format or resolve_log_format()
    handler = logging.StreamHandler(stream or sys.stderr)
    if resolved_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))

    root = logging.getLogger("dce")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(resolved_level)
    root.propagate = False
    _CONFIGURED = True


def reset_logging_for_tests() -> None:
    """Clear configuration flag (unit tests only)."""
    global _CONFIGURED
    _CONFIGURED = False
    logging.getLogger("dce").handlers.clear()
