from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

_DEFAULT_EVENT_PATH = Path("data/error_events.jsonl")
_DEFAULT_HEARTBEAT_DIR = Path("data/heartbeats")
_WRITE_LOCK = threading.Lock()
_SECRET_KEY = re.compile(
    r"(token|secret|password|passwd|api[_-]?key|service[_-]?role|webhook)",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._-]+|https://[^\s/]+/api/webhooks/[^\s]+"
    r"|(?:sk|eyJ)[a-z0-9._-]{12,})"
)
_HOME = str(Path.home())


class EventStatus:
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    RECOVERED = "recovered"
    HEARTBEAT = "heartbeat"


class Severity:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_message(value: str) -> str:
    value = re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27,}", "<uuid>", value, flags=re.I)
    value = re.sub(r"\b\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+", "<time>", value)
    value = re.sub(r"\b\d+\b", "<n>", value)
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value[:500]


def _redact_string(value: str) -> str:
    if _HOME and value.startswith(_HOME):
        value = "~" + value[len(_HOME) :]
    return _SECRET_VALUE.sub("<redacted>", value)


def sanitize(value: Any, *, key: str = "") -> Any:
    if _SECRET_KEY.search(key):
        return "<redacted>"
    if isinstance(value, Mapping):
        return {str(k): sanitize(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize(v) for v in value]
    if isinstance(value, Path):
        return _redact_string(str(value))
    if isinstance(value, str):
        return _redact_string(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact_string(repr(value))


def make_fingerprint(
    category: str,
    component: str,
    operation: str,
    code: str,
    message: str,
) -> str:
    canonical = "|".join(
        [category, component, operation, code, _normalize_message(message)]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class OperationalEventLog:
    """Append-only, privacy-aware structured operational event log."""

    def __init__(self, path: Path | str | None = None) -> None:
        configured = os.environ.get("VLOG_ERROR_EVENT_FILE")
        self.path = Path(path or configured or _DEFAULT_EVENT_PATH)

    def emit(
        self,
        *,
        category: str,
        component: str,
        operation: str,
        status: str,
        severity: str = Severity.INFO,
        message: str,
        code: str = "",
        run_id: str | None = None,
        session_id: str | None = None,
        retryable: bool | None = None,
        context: Mapping[str, Any] | None = None,
        error: BaseException | str | None = None,
        source: str = "application",
    ) -> dict[str, Any]:
        error_type = ""
        error_message = ""
        if isinstance(error, BaseException):
            error_type = type(error).__name__
            error_message = str(error)
        elif error:
            error_type = "Error"
            error_message = str(error)

        effective_message = error_message or message
        effective_code = code or error_type or operation
        payload: dict[str, Any] = {
            "schema_version": 1,
            "event_id": str(uuid4()),
            "timestamp": _utc_now(),
            "category": category,
            "component": component,
            "operation": operation,
            "status": status,
            "severity": severity,
            "code": effective_code,
            "message": _redact_string(message),
            "run_id": run_id or os.environ.get("VLOG_RUN_ID"),
            "session_id": session_id,
            "task_name": os.environ.get("VLOG_TASK_NAME"),
            "retryable": retryable,
            "source": source,
            "host": socket.gethostname(),
            "platform": platform.system().lower(),
            "pid": os.getpid(),
            "context": sanitize(dict(context or {})),
            "error": {
                "type": error_type,
                "message": _redact_string(error_message),
            }
            if error_message
            else None,
            "fingerprint": make_fingerprint(
                category,
                component,
                operation,
                effective_code,
                effective_message,
            ),
        }
        self._append(payload)
        return payload

    def heartbeat(
        self,
        *,
        component: str,
        status: str = "healthy",
        context: Mapping[str, Any] | None = None,
    ) -> Path:
        heartbeat_dir = Path(
            os.environ.get("VLOG_HEARTBEAT_DIR", str(_DEFAULT_HEARTBEAT_DIR))
        )
        target = heartbeat_dir / f"{component}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "timestamp": _utc_now(),
            "component": component,
            "status": status,
            "pid": os.getpid(),
            "context": sanitize(dict(context or {})),
        }
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(target)
        return target

    def _append(self, payload: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")
        with _WRITE_LOCK:
            fd = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                os.write(fd, encoded)
                os.fsync(fd)
            finally:
                os.close(fd)


class TraceLogger:
    def __init__(self) -> None:
        from src.infrastructure.settings import settings

        self._log_path = Path(settings.trace_file)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        component: str,
        model: str,
        start_time: float,
        input_text: str,
        output_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": os.environ.get("VLOG_RUN_ID"),
            "task_name": os.environ.get("VLOG_TASK_NAME"),
            "component": component,
            "model": model,
            "latency": round(time.time() - start_time, 4),
            "input_chars": len(input_text),
            "output_chars": len(output_text),
            "metadata": sanitize(metadata or {}),
        }
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


_default_log = OperationalEventLog()


def emit_event(**kwargs: Any) -> dict[str, Any]:
    return _default_log.emit(**kwargs)
