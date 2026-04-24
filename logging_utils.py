"""
Logging utilities for JARVIS.

This module provides:
- `setup_logging(config)` for consistent console + rotating file logging
- A lightweight structured logger (`get_logger`) used as `audit_log.info("event", k=v)`
- Trace context helpers (`bind_trace_id`, `get_trace_id`, `new_trace_id`, `clear_trace_context`)
"""

from __future__ import annotations

import contextvars
import json
import logging
import logging.handlers
import os
import sys
import uuid
from pathlib import Path
from typing import Any


_TRACE_ID: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")
_LOGGER_CACHE: dict[str, "EventLogger"] = {}


def new_trace_id() -> str:
    return uuid.uuid4().hex


def bind_trace_id(trace_id: str | None = None, **_fields: Any) -> str:
    # `_fields` is accepted for call-site compatibility; we only bind the id.
    trace_id = str(trace_id or new_trace_id()).strip()
    _TRACE_ID.set(trace_id)
    return trace_id


def get_trace_id() -> str:
    return str(_TRACE_ID.get() or "")


def clear_trace_context() -> None:
    _TRACE_ID.set("")


def _safe_json_dumps(payload: dict[str, Any]) -> str:
    def _default(obj: Any) -> str:
        try:
            return str(obj)
        except Exception:
            return "<unserializable>"

    return json.dumps(
        payload,
        ensure_ascii=True,
        default=_default,
        separators=(",", ":"),
    )


class EventLogger:
    """
    Minimal structured logger wrapper.

    Supports calls like: `log.info("event_name", key=value, ...)`.
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
        self.name = name

    def _emit(self, level: int, event: str, **fields: Any) -> None:
        payload: dict[str, Any] = {"event": str(event or "").strip() or "event"}
        trace_id = get_trace_id()
        if trace_id and "trace_id" not in fields:
            fields["trace_id"] = trace_id
        if fields:
            payload.update(fields)
        self._logger.log(level, _safe_json_dumps(payload))

    def debug(self, event: str, **fields: Any) -> None:
        self._emit(logging.DEBUG, event, **fields)

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._emit(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self._emit(logging.ERROR, event, **fields)

    def exception(self, event: str, **fields: Any) -> None:
        payload: dict[str, Any] = {"event": str(event or "").strip() or "exception"}
        trace_id = get_trace_id()
        if trace_id and "trace_id" not in fields:
            fields["trace_id"] = trace_id
        if fields:
            payload.update(fields)
        self._logger.exception(_safe_json_dumps(payload))

    @property
    def logger(self) -> logging.Logger:
        return self._logger


def get_logger(name: str) -> EventLogger:
    safe = str(name or "jarvis").strip() or "jarvis"
    if safe not in _LOGGER_CACHE:
        _LOGGER_CACHE[safe] = EventLogger(safe)
    return _LOGGER_CACHE[safe]


def _cfg_get(config: Any, key: str, default: Any) -> Any:
    if config is None:
        return default
    getter = getattr(config, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except TypeError:
            try:
                return getter(key)  # type: ignore[misc]
            except Exception:
                return default
        except Exception:
            return default
    if isinstance(config, dict):
        return config.get(key, default)
    return default


def setup_logging(config: Any) -> None:
    log_dir = Path(str(_cfg_get(config, "logging.path", "logs")))
    log_dir.mkdir(parents=True, exist_ok=True)

    level_name = str(_cfg_get(config, "logging.level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    max_bytes = int(_cfg_get(config, "logging.max_bytes", 10 * 1024 * 1024))
    backup_count = int(_cfg_get(config, "logging.backup_count", 5))
    file_name = str(_cfg_get(config, "logging.file", "jarvis.log")).strip() or "jarvis.log"

    log_file = Path(file_name)
    if not log_file.is_absolute():
        log_file = log_dir / log_file

    error_file = log_dir / "jarvis_errors.log"

    # Ensure console streams use UTF-8 so logs don't crash on Windows encodings.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicates on reload.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    err_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=max(1, max_bytes // 2),
        backupCount=max(1, backup_count),
        encoding="utf-8",
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)
    root.addHandler(err_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    get_logger(__name__).info(
        "logging_initialized",
        log_level=level_name,
        file=str(log_file),
        pid=os.getpid(),
    )


__all__ = [
    "EventLogger",
    "bind_trace_id",
    "clear_trace_context",
    "get_logger",
    "get_trace_id",
    "new_trace_id",
    "setup_logging",
]
