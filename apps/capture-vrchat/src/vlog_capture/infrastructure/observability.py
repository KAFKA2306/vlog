from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import socket
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping
from uuid import uuid4

try:
    import fcntl
except ImportError:  # pragma: no cover - production is WSL/Linux
    fcntl: Any = None

_DEFAULT_EVENT_PATH = Path("data/error_events.jsonl")
_DEFAULT_HEARTBEAT_DIR = Path("data/heartbeats")
_DEFAULT_MAX_BYTES = 10 * 1024 * 1024
_DEFAULT_BACKUPS = 7
_DEFAULT_RETENTION_DAYS = 90
_WRITE_LOCK = threading.Lock()
_SECRET_KEY = re.compile(
    r"(token|secret|password|passwd|api[_-]?key|service[_-]?role|webhook)",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._~+/-]+|https://[^\s/]+/api/webhooks/[^\s]+"
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


_SEVERITY_NUMBER = {
    Severity.INFO: 9,
    Severity.WARNING: 13,
    Severity.ERROR: 17,
    Severity.CRITICAL: 21,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_message(value: str) -> str:
    value = re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27,}", "<uuid>", value, flags=re.I)
    value = re.sub(r"\b\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+", "<time>", value)
    value = re.sub(r"\b\d+\b", "<n>", value)
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value[:500]


def _redact_string(value: str) -> str:
    if _HOME:
        value = value.replace(_HOME, "~")
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


def systemd_notify(*fields: str) -> bool:
    """Send an sd_notify datagram without adding a runtime dependency."""
    address = os.environ.get("NOTIFY_SOCKET")
    if not address or not fields:
        return False
    if address.startswith("@"):
        address = "\0" + address[1:]
    payload = "\n".join(field for field in fields if field).encode("utf-8")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
            client.connect(address)
            client.sendall(payload)
        return True
    except OSError:
        return False


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("event log write made no progress")
        view = view[written:]


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


class OperationalEventLog:
    """Append-only, privacy-aware structured event log for WSL services."""

    def __init__(self, path: Path | str | None = None) -> None:
        configured = os.environ.get("VLOG_ERROR_EVENT_FILE")
        self.path = Path(path or configured or _DEFAULT_EVENT_PATH)
        self.max_bytes = int(
            os.environ.get("VLOG_EVENT_MAX_BYTES", str(_DEFAULT_MAX_BYTES))
        )
        self.backups = max(
            1, int(os.environ.get("VLOG_EVENT_BACKUPS", str(_DEFAULT_BACKUPS)))
        )
        self.retention_days = max(
            1,
            int(
                os.environ.get(
                    "VLOG_EVENT_RETENTION_DAYS", str(_DEFAULT_RETENTION_DAYS)
                )
            ),
        )

    @property
    def lock_path(self) -> Path:
        return self.path.with_name(self.path.name + ".lock")

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
        resource_id: str | None = None,
        resolves_fingerprint: str | None = None,
        retryable: bool | None = None,
        context: Mapping[str, Any] | None = None,
        error: BaseException | str | None = None,
        source: str = "application",
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> dict[str, Any]:
        error_type = ""
        error_message = ""
        stacktrace = ""
        if isinstance(error, BaseException):
            error_type = type(error).__name__
            error_message = str(error)
            stacktrace = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )[-16000:]
        elif error:
            error_type = "Error"
            error_message = str(error)

        effective_message = error_message or message
        effective_code = code or error_type or operation
        payload: dict[str, Any] = {
            "schema_version": 2,
            "event_id": str(uuid4()),
            "timestamp": _utc_now(),
            "severity_text": severity,
            "severity_number": _SEVERITY_NUMBER.get(severity, 17),
            "category": category,
            "component": component,
            "operation": operation,
            "status": status,
            "code": effective_code,
            "message": _redact_string(message),
            "run_id": run_id or os.environ.get("VLOG_RUN_ID"),
            "session_id": session_id,
            "resource_id": resource_id,
            "resolves_fingerprint": resolves_fingerprint,
            "task_name": os.environ.get("VLOG_TASK_NAME"),
            "retryable": retryable,
            "source": source,
            "service": {
                "name": os.environ.get("VLOG_SERVICE_NAME", "vlog"),
                "instance_id": socket.gethostname(),
                "version": os.environ.get("VLOG_SERVICE_VERSION", "unknown"),
            },
            "host": socket.gethostname(),
            "platform": platform.system().lower(),
            "pid": os.getpid(),
            "trace_id": trace_id,
            "span_id": span_id,
            "context": sanitize(dict(context or {})),
            "exception": {
                "type": error_type,
                "message": _redact_string(error_message),
                "stacktrace": _redact_string(stacktrace),
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

    def recover_latest(
        self,
        *,
        category: str,
        component: str,
        operation: str,
        resource_id: str | None = None,
        message: str,
        code: str = "recovered",
        run_id: str | None = None,
        session_id: str | None = None,
        context: Mapping[str, Any] | None = None,
        source: str = "application",
    ) -> dict[str, Any] | None:
        target = self._latest_open_failure(
            category=category,
            component=component,
            operation=operation,
            resource_id=resource_id,
        )
        if target is None:
            return None
        return self.emit(
            category=category,
            component=component,
            operation=operation,
            status=EventStatus.RECOVERED,
            severity=Severity.INFO,
            message=message,
            code=code,
            run_id=run_id,
            session_id=session_id,
            resource_id=resource_id,
            resolves_fingerprint=str(target["fingerprint"]),
            retryable=False,
            context=context,
            source=source,
        )

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
            "schema_version": 2,
            "timestamp": _utc_now(),
            "component": component,
            "status": status,
            "pid": os.getpid(),
            "context": sanitize(dict(context or {})),
        }
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary, target)
        return target

    def _latest_open_failure(
        self,
        *,
        category: str,
        component: str,
        operation: str,
        resource_id: str | None,
    ) -> dict[str, Any] | None:
        open_failures: dict[tuple[str, str | None], dict[str, Any]] = {}
        for event in self.iter_events():
            event_resource = (
                str(event.get("resource_id"))
                if event.get("resource_id") is not None
                else None
            )
            if (
                event.get("status") == EventStatus.FAILED
                and event.get("category") == category
                and event.get("component") == component
                and event.get("operation") == operation
                and event_resource == resource_id
            ):
                key = (str(event.get("fingerprint") or ""), event_resource)
                open_failures[key] = event
            elif event.get("status") == EventStatus.RECOVERED and event.get(
                "resolves_fingerprint"
            ):
                key = (str(event["resolves_fingerprint"]), event_resource)
                open_failures.pop(key, None)
        return next(reversed(open_failures.values()), None)

    def iter_events(self) -> Iterator[dict[str, Any]]:
        paths = [self.path]
        paths.extend(
            self.path.with_name(f"{self.path.name}.{index}")
            for index in range(1, self.backups + 1)
        )
        for path in reversed(paths):
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for raw in handle:
                    try:
                        value = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(value, dict):
                        yield value

    def _append(self, payload: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
        encoded = line.encode("utf-8")
        with _WRITE_LOCK, _exclusive_lock(self.lock_path):
            self._rotate_if_needed(len(encoded))
            fd = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                _write_all(fd, encoded)
                if self._should_fsync(payload):
                    os.fsync(fd)
            finally:
                os.close(fd)
            self._prune_expired_backups()

    def _rotate_if_needed(self, incoming_bytes: int) -> None:
        if not self.path.exists():
            return
        if self.path.stat().st_size + incoming_bytes <= self.max_bytes:
            return
        oldest = self.path.with_name(f"{self.path.name}.{self.backups}")
        oldest.unlink(missing_ok=True)
        for index in range(self.backups - 1, 0, -1):
            source = self.path.with_name(f"{self.path.name}.{index}")
            if source.exists():
                source.replace(self.path.with_name(f"{self.path.name}.{index + 1}"))
        self.path.replace(self.path.with_name(f"{self.path.name}.1"))

    def _prune_expired_backups(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        for index in range(1, self.backups + 1):
            path = self.path.with_name(f"{self.path.name}.{index}")
            if not path.exists():
                continue
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            if modified < cutoff:
                path.unlink(missing_ok=True)

    @staticmethod
    def _should_fsync(payload: Mapping[str, Any]) -> bool:
        policy = os.environ.get("VLOG_EVENT_FSYNC", "failures").lower()
        if policy == "always":
            return True
        if policy == "never":
            return False
        return (
            payload.get("status")
            in {
                EventStatus.FAILED,
                EventStatus.RECOVERED,
            }
            or payload.get("severity_text") == Severity.CRITICAL
        )


class TraceLogger:
    def __init__(self) -> None:
        from vlog_capture.infrastructure.settings import settings

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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
