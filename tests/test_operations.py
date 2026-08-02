from pathlib import Path

from src.infrastructure.observability import EventStatus, OperationalEventLog, Severity
from src.operations import OperationsLoader, build_report, render_html


def test_event_redacts_and_report_resolves(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log = OperationalEventLog(tmp_path / "data/error_events.jsonl")
    log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.FAILED,
        severity=Severity.CRITICAL,
        message="failed with token sk-abcdefghijklmnop",
        code="recording_start_failed",
        context={"api_key": "secret", "path": str(Path.home() / "x")},
    )
    log.emit(
        category="recording",
        component="audio-recorder",
        operation="start",
        status=EventStatus.SUCCEEDED,
        severity=Severity.INFO,
        message="recording started",
        code="recording_start",
    )
    raw = (tmp_path / "data/error_events.jsonl").read_text(encoding="utf-8")
    assert "abcdefghijklmnop" not in raw
    assert "<redacted>" in raw
    report = build_report(OperationsLoader(tmp_path).load(90), 90)
    assert report.open_incidents == 0
    assert "VLog Operations" in render_html(report)


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
