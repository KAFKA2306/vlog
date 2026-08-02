import json
from pathlib import Path

from src.infrastructure.observability import EventStatus, OperationalEventLog, Severity
from src.operations import OperationsLoader, build_report, render_html


def test_success_does_not_resolve_failure(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = OperationalEventLog(tmp_path / "data/error_events.jsonl")
    failure = log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.FAILED,
        severity=Severity.CRITICAL,
        message="input unavailable",
        code="recording_start_failed",
        resource_id="audio-input:default",
    )
    log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.SUCCEEDED,
        severity=Severity.INFO,
        message="another input started",
        code="recording_start",
        resource_id="audio-input:other",
    )
    report = build_report(OperationsLoader(tmp_path).load(90), 90)
    assert report.open_incidents == 1
    assert report.incidents[0].fingerprint == failure["fingerprint"]


def test_explicit_recovery_resolves_exact_fingerprint_and_resource(
    tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    log = OperationalEventLog(tmp_path / "data/error_events.jsonl")
    first = log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.FAILED,
        severity=Severity.CRITICAL,
        message="input unavailable",
        code="recording_start_failed",
        resource_id="audio-input:default",
    )
    second = log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.FAILED,
        severity=Severity.CRITICAL,
        message="permission denied",
        code="recording_permission_failed",
        resource_id="audio-input:other",
    )
    recovery = log.recover_latest(
        category="recording",
        component="audio-recorder",
        operation="start",
        resource_id="audio-input:default",
        message="default input verified",
    )
    assert recovery is not None
    assert recovery["resolves_fingerprint"] == first["fingerprint"]
    report = build_report(OperationsLoader(tmp_path).load(90), 90)
    states = {incident.fingerprint: incident.is_open for incident in report.incidents}
    assert states[first["fingerprint"]] is False
    assert states[second["fingerprint"]] is True
    assert "VLog Operations" in render_html(report)


def test_failure_recurrence_after_recovery_reopens_incident(
    tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    log = OperationalEventLog(tmp_path / "data/error_events.jsonl")
    first = log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.FAILED,
        severity=Severity.CRITICAL,
        message="input unavailable",
        code="recording_start_failed",
        resource_id="audio-input:default",
    )
    assert log.recover_latest(
        category="recording",
        component="audio-recorder",
        operation="start",
        resource_id="audio-input:default",
        message="input recovered",
    )
    second = log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.FAILED,
        severity=Severity.CRITICAL,
        message="input unavailable",
        code="recording_start_failed",
        resource_id="audio-input:default",
    )
    assert first["fingerprint"] == second["fingerprint"]
    report = build_report(OperationsLoader(tmp_path).load(90), 90)
    assert report.open_incidents == 1
    assert report.incidents[0].count == 2


def test_event_redacts_secrets_and_exception_stack(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = OperationalEventLog(tmp_path / "data/error_events.jsonl")
    try:
        raise RuntimeError("token sk-abcdefghijklmnop")
    except RuntimeError as exc:
        log.emit(
            category="generation",
            component="gemini",
            operation="generate",
            status=EventStatus.FAILED,
            severity=Severity.ERROR,
            message="provider failed",
            code="provider_error",
            context={"api_key": "secret", "path": str(Path.home() / "x")},
            error=exc,
        )
    raw = (tmp_path / "data/error_events.jsonl").read_text(encoding="utf-8")
    assert "abcdefghijklmnop" not in raw
    assert '"api_key":"<redacted>"' in raw
    payload = json.loads(raw)
    assert payload["exception"]["type"] == "RuntimeError"
    assert "stacktrace" in payload["exception"]


def test_corrupt_jsonl_is_visible_as_incident(tmp_path: Path):
    path = tmp_path / "data/error_events.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("{broken\n", encoding="utf-8")
    report = build_report(OperationsLoader(tmp_path).load(90), 90)
    assert report.open_incidents == 1
    assert report.incidents[0].code == "invalid_jsonl"


def test_legacy_patterns_are_classified(tmp_path: Path):
    log_path = tmp_path / "data/logs/vlog.log"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "2026-06-20 10:00:00 [ERROR] Gemini 429 RESOURCE_EXHAUSTED\n"
        "2026-07-27 05:30:00 [ERROR] /snap/bin/task: not found\n",
        encoding="utf-8",
    )
    events = OperationsLoader(tmp_path).load(120)
    codes = {event["code"] for event in events}
    assert "provider_rate_limited" in codes
    assert "scheduler_binary_missing" in codes
