import json
import multiprocessing
import os
import socket
from pathlib import Path

from src.infrastructure.observability import (
    EventStatus,
    OperationalEventLog,
    Severity,
    systemd_notify,
)


def _write_events(path: str, worker: int, count: int) -> None:
    os.environ["VLOG_EVENT_FSYNC"] = "never"
    log = OperationalEventLog(path)
    for index in range(count):
        log.emit(
            category="infrastructure",
            component="concurrency-test",
            operation="append",
            status=EventStatus.SUCCEEDED,
            severity=Severity.INFO,
            message=f"worker={worker} index={index}",
            code="append_test",
            resource_id=str(worker),
        )


def test_multiprocess_append_produces_complete_json_lines(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    processes = [
        multiprocessing.Process(target=_write_events, args=(str(path), worker, 40))
        for worker in range(4)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=20)
        assert process.exitcode == 0

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 160
    payloads = [json.loads(line) for line in lines]
    assert len({payload["event_id"] for payload in payloads}) == 160


def test_log_rotation_preserves_readable_events(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("VLOG_EVENT_MAX_BYTES", "900")
    monkeypatch.setenv("VLOG_EVENT_BACKUPS", "3")
    monkeypatch.setenv("VLOG_EVENT_FSYNC", "never")
    path = tmp_path / "events.jsonl"
    log = OperationalEventLog(path)
    for index in range(20):
        log.emit(
            category="infrastructure",
            component="rotation-test",
            operation="append",
            status=EventStatus.SUCCEEDED,
            severity=Severity.INFO,
            message=f"event {index} " + ("x" * 100),
            code="rotation_test",
        )
    assert path.exists()
    assert path.with_name("events.jsonl.1").exists()
    events = list(log.iter_events())
    assert events
    assert all(event["component"] == "rotation-test" for event in events)


def test_systemd_notify_sends_datagram(tmp_path: Path, monkeypatch):
    socket_path = tmp_path / "notify.sock"
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(str(socket_path))
    server.settimeout(2)
    try:
        monkeypatch.setenv("NOTIFY_SOCKET", str(socket_path))
        assert systemd_notify("READY=1", "WATCHDOG=1") is True
        assert server.recv(1024).decode("utf-8") == "READY=1\nWATCHDOG=1"
    finally:
        server.close()
