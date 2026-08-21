# ruff: noqa: E501
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import webbrowser
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from vlog_capture.infrastructure.observability import (
    EventStatus,
    OperationalEventLog,
    Severity,
    make_fingerprint,
    sanitize,
)
from vlog_capture.portability import runtime_directories

CATEGORY_ORDER = [
    "monitoring",
    "recording",
    "transcription",
    "processing",
    "generation",
    "sync",
    "notification",
    "scheduler",
    "infrastructure",
]
SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2, "critical": 3}
STATUS_SUCCESS = {EventStatus.SUCCEEDED, EventStatus.RECOVERED}
STATUS_FAILURE = {EventStatus.FAILED}


@dataclass(frozen=True)
class Incident:
    key: tuple[str, str | None]
    category: str
    component: str
    operation: str
    severity: str
    code: str
    count: int
    first_seen: datetime
    last_seen: datetime
    message: str
    fingerprint: str
    resource_id: str | None
    is_open: bool
    context: Mapping[str, Any]


@dataclass(frozen=True)
class OperationsReport:
    generated_at: datetime
    days: int
    events: tuple[dict[str, Any], ...]
    incidents: tuple[Incident, ...]

    @property
    def failures(self) -> int:
        return sum(1 for event in self.events if event.get("status") in STATUS_FAILURE)

    @property
    def successes(self) -> int:
        return sum(1 for event in self.events if event.get("status") in STATUS_SUCCESS)

    @property
    def reliability(self) -> float:
        total = self.failures + self.successes
        return self.successes / total * 100.0 if total else 100.0

    @property
    def open_incidents(self) -> int:
        return sum(incident.is_open for incident in self.incidents)

    @property
    def state(self) -> str:
        if any(i.is_open and i.severity == Severity.CRITICAL for i in self.incidents):
            return "critical"
        if self.open_incidents or self.reliability < 95:
            return "degraded"
        return "healthy"


class OperationsLoader:
    def __init__(self, root: Path | None = None) -> None:
        # Explicit roots preserve the legacy test/import layout; production uses state home.
        self.root = (
            (root / "data") if root is not None else runtime_directories().state
        ).resolve()

    def load(self, days: int) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        events: list[dict[str, Any]] = []
        event_path = self.root / "error_events.jsonl"
        rotated = sorted(
            event_path.parent.glob(event_path.name + ".*"),
            key=self._rotation_index,
            reverse=True,
        )
        for path in rotated:
            if path.name.endswith(".lock"):
                continue
            events.extend(self._load_jsonl(path))
        events.extend(self._load_jsonl(event_path))
        events.extend(self._load_incidents(self.root / "incidents.jsonl"))
        events.extend(self._load_daily_runs(self.root / "daily_runs.jsonl"))
        events.extend(self._load_legacy_log(self.root / "logs/vlog.log"))
        filtered = [event for event in events if self._timestamp(event) >= cutoff]
        filtered.sort(key=self._timestamp)
        return self._dedupe(filtered)

    @staticmethod
    def _rotation_index(path: Path) -> int:
        try:
            return int(path.name.rsplit(".", 1)[-1])
        except ValueError:
            return -1

    def _load_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        events: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "category": "infrastructure",
                        "component": "event-log",
                        "operation": "parse",
                        "status": EventStatus.FAILED,
                        "severity_text": Severity.WARNING,
                        "code": "invalid_jsonl",
                        "message": f"Invalid JSONL at {path.name}:{line_no}",
                        "resource_id": path.name,
                        "context": {"line": raw[:160]},
                    }
                events.append(self._canonical(payload, source=str(path)))
        return events

    def _load_incidents(self, path: Path) -> list[dict[str, Any]]:
        events = self._load_jsonl(path)
        for event in events:
            if event.get("status") in {"open", "active", "error"}:
                event["status"] = EventStatus.FAILED
            elif event.get("status") in {"closed", "resolved"}:
                event["status"] = EventStatus.RECOVERED
                if not event.get("resolves_fingerprint"):
                    event["resolves_fingerprint"] = event.get("fingerprint")
        return events

    def _load_daily_runs(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        events: list[dict[str, Any]] = []
        for payload in self._read_jsonl(path):
            task = str(payload.get("task_name") or "daily")
            prefix = task.split(":", 1)[0]
            category = {
                "transcribe": "transcription",
                "summarize": "generation",
                "novel": "generation",
                "sync": "sync",
                "audit": "processing",
            }.get(prefix, "scheduler")
            status = {
                "try": EventStatus.STARTED,
                "success": EventStatus.SUCCEEDED,
                "failed": EventStatus.FAILED,
            }.get(str(payload.get("status")), str(payload.get("status") or "started"))
            events.append(
                self._canonical(
                    {
                        "timestamp": payload.get("timestamp"),
                        "category": category,
                        "component": "daily-pipeline",
                        "operation": task,
                        "status": status,
                        "severity_text": Severity.ERROR
                        if status == EventStatus.FAILED
                        else Severity.INFO,
                        "code": f"daily_{prefix}_{status}",
                        "message": str(
                            payload.get("error") or f"Daily stage {task}: {status}"
                        ),
                        "run_id": payload.get("run_id"),
                        "resource_id": task,
                        "context": {
                            "expected_components": payload.get("expected_components"),
                            "verification": payload.get("verification"),
                        },
                    },
                    source=str(path),
                )
            )
        return events

    def _load_legacy_log(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        timestamp_re = re.compile(r"^(\d{4}-\d{2}-\d{2}[ T][0-9:.,+-]+)")
        events: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, raw in enumerate(handle, start=1):
                lower = raw.lower()
                if not any(
                    token in lower
                    for token in (
                        "error",
                        "failed",
                        "exception",
                        "traceback",
                        "warning",
                        "429",
                    )
                ):
                    continue
                match = timestamp_re.search(raw)
                timestamp = match.group(1).replace(",", ".") if match else None
                category, component, operation, code = self._classify_legacy(raw)
                severity = (
                    Severity.ERROR
                    if any(
                        token in lower
                        for token in (
                            "error",
                            "failed",
                            "exception",
                            "traceback",
                            "429",
                        )
                    )
                    else Severity.WARNING
                )
                events.append(
                    self._canonical(
                        {
                            "timestamp": timestamp,
                            "category": category,
                            "component": component,
                            "operation": operation,
                            "status": EventStatus.FAILED,
                            "severity_text": severity,
                            "code": code,
                            "message": raw.strip()[:800],
                            "context": {"line_no": line_no},
                        },
                        source=str(path),
                    )
                )
        return events

    @staticmethod
    def _classify_legacy(message: str) -> tuple[str, str, str, str]:
        lower = message.lower()
        if "429" in lower or "resource_exhausted" in lower or "quota" in lower:
            return "generation", "gemini", "generate", "provider_rate_limited"
        if "/snap/bin/task" in lower or "task: not found" in lower:
            return "scheduler", "systemd", "launch", "scheduler_binary_missing"
        if "record" in lower or "sounddevice" in lower or "inputstream" in lower:
            return "recording", "audio-recorder", "record", "recording_failure"
        if "whisper" in lower or "transcrib" in lower:
            return "transcription", "whisper", "transcribe", "transcription_failure"
        if "supabase" in lower or "sync" in lower:
            return "sync", "supabase", "sync", "sync_failure"
        if "discord" in lower or "notify" in lower:
            return "notification", "discord", "notify", "notification_failure"
        return "infrastructure", "legacy-log", "runtime", "legacy_runtime_failure"

    @staticmethod
    def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw in handle:
                if not raw.strip():
                    continue
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    yield value

    def _canonical(self, payload: Mapping[str, Any], source: str) -> dict[str, Any]:
        event = dict(payload)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        event.setdefault("category", "infrastructure")
        event.setdefault("component", "unknown")
        event.setdefault("operation", "unknown")
        event.setdefault("status", EventStatus.FAILED)
        event.setdefault("severity_text", event.get("severity", Severity.ERROR))
        event.setdefault("code", str(event.get("operation")))
        event.setdefault("message", str(event.get("error") or event.get("code")))
        event.setdefault("resource_id", None)
        event.setdefault("resolves_fingerprint", None)
        event.setdefault("context", {})
        event.setdefault("source", source)
        event["context"] = sanitize(event.get("context") or {})
        event["message"] = str(sanitize(str(event.get("message") or "")))
        event.setdefault(
            "fingerprint",
            make_fingerprint(
                str(event["category"]),
                str(event["component"]),
                str(event["operation"]),
                str(event["code"]),
                str(event["message"]),
            ),
        )
        return event

    @staticmethod
    def _timestamp(event: Mapping[str, Any]) -> datetime:
        raw = str(event.get("timestamp") or "")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _dedupe(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen_ids: set[str] = set()
        seen_legacy: set[tuple[str, str, str, str, str]] = set()
        output: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event.get("event_id") or "")
            if event_id:
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
            else:
                key = (
                    self._timestamp(event).isoformat(),
                    str(event.get("component")),
                    str(event.get("operation")),
                    str(event.get("status")),
                    str(event.get("message"))[:200],
                )
                if key in seen_legacy:
                    continue
                seen_legacy.add(key)
            output.append(event)
        return output


def build_report(events: list[dict[str, Any]], days: int) -> OperationsReport:
    failures_by_key: dict[tuple[str, str | None], list[dict[str, Any]]] = defaultdict(
        list
    )
    latest_failure_index: dict[tuple[str, str | None], int] = {}
    latest_recovery_index: dict[tuple[str, str | None], int] = {}

    for index, event in enumerate(events):
        resource_id = (
            str(event.get("resource_id"))
            if event.get("resource_id") is not None
            else None
        )
        if event.get("status") in STATUS_FAILURE:
            key = (str(event.get("fingerprint") or ""), resource_id)
            failures_by_key[key].append(event)
            latest_failure_index[key] = index
        elif event.get("status") == EventStatus.RECOVERED and event.get(
            "resolves_fingerprint"
        ):
            key = (str(event["resolves_fingerprint"]), resource_id)
            latest_recovery_index[key] = index

    incidents: list[Incident] = []
    for key, failures in failures_by_key.items():
        failures.sort(key=OperationsLoader._timestamp)
        first_failure, last_failure = failures[0], failures[-1]
        severity = max(
            (
                str(
                    event.get("severity_text")
                    or event.get("severity")
                    or Severity.ERROR
                )
                for event in failures
            ),
            key=lambda value: SEVERITY_RANK.get(value, 2),
        )
        fingerprint, resource_id = key
        incidents.append(
            Incident(
                key=key,
                category=str(last_failure.get("category") or "infrastructure"),
                component=str(last_failure.get("component") or "unknown"),
                operation=str(last_failure.get("operation") or "unknown"),
                severity=severity,
                code=str(last_failure.get("code") or "failure"),
                count=len(failures),
                first_seen=OperationsLoader._timestamp(first_failure),
                last_seen=OperationsLoader._timestamp(last_failure),
                message=str(last_failure.get("message") or ""),
                fingerprint=fingerprint,
                resource_id=resource_id,
                is_open=latest_failure_index[key] > latest_recovery_index.get(key, -1),
                context=dict(last_failure.get("context") or {}),
            )
        )
    incidents.sort(
        key=lambda incident: (
            incident.is_open,
            SEVERITY_RANK.get(incident.severity, 2),
            incident.count,
            incident.last_seen,
        ),
        reverse=True,
    )
    return OperationsReport(
        generated_at=datetime.now(timezone.utc),
        days=days,
        events=tuple(events),
        incidents=tuple(incidents),
    )


def _fmt_time(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M")


def print_report(report: OperationsReport) -> None:
    print(f"VLOG OPERATIONS  {report.state.upper()}  window={report.days}d")
    print(
        f"reliability={report.reliability:.1f}%  failures={report.failures}  open_incidents={report.open_incidents}  events={len(report.events)}"
    )
    print("-")
    if not report.incidents:
        print("No incidents found in the selected window.")
        return
    print(f"{'STATE':8} {'SEV':8} {'COUNT':5} {'LAST':16} {'RESOURCE':18} ISSUE")
    for incident in report.incidents[:30]:
        state_text = "OPEN" if incident.is_open else "RESOLVED"
        issue = f"{incident.component}/{incident.operation}: {incident.message}"
        print(
            f"{state_text:8} {incident.severity.upper():8} {incident.count:5d} {_fmt_time(incident.last_seen):16} {(incident.resource_id or '-'):18.18} {issue[:100]}"
        )


def report_to_dict(report: OperationsReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "days": report.days,
        "state": report.state,
        "reliability": round(report.reliability, 2),
        "failures": report.failures,
        "successes": report.successes,
        "open_incidents": report.open_incidents,
        "events": list(report.events),
        "incidents": [
            {
                "category": incident.category,
                "component": incident.component,
                "operation": incident.operation,
                "severity": incident.severity,
                "code": incident.code,
                "count": incident.count,
                "first_seen": incident.first_seen.isoformat(),
                "last_seen": incident.last_seen.isoformat(),
                "message": incident.message,
                "fingerprint": incident.fingerprint,
                "resource_id": incident.resource_id,
                "is_open": incident.is_open,
                "context": incident.context,
            }
            for incident in report.incidents
        ],
    }


def render_html(report: OperationsReport) -> str:
    category_counts = Counter(str(event.get("category")) for event in report.events)
    category_failures = Counter(
        str(event.get("category"))
        for event in report.events
        if event.get("status") == EventStatus.FAILED
    )
    state_label = {"healthy": "正常", "degraded": "要確認", "critical": "重大障害"}[
        report.state
    ]

    stages = "".join(
        f"<div class='stage'><span>{html.escape(category)}</span><strong>{category_failures.get(category, 0)}</strong><small>fail / {category_counts.get(category, 0)} events</small></div>"
        for category in CATEGORY_ORDER
    )
    incidents = []
    for incident in report.incidents[:80]:
        state = "未解消" if incident.is_open else "解消済み"
        context = html.escape(
            json.dumps(incident.context, ensure_ascii=False, indent=2)
        )
        incidents.append(
            "<tr>"
            f"<td><span class='pill {'open' if incident.is_open else 'resolved'}'>{state}</span></td>"
            f"<td>{html.escape(incident.severity)}</td>"
            f"<td>{html.escape(incident.category)}</td>"
            f"<td><strong>{html.escape(incident.component)}</strong><br><small>{html.escape(incident.operation)}</small></td>"
            f"<td><code>{html.escape(incident.resource_id or '-')}</code></td>"
            f"<td>{incident.count}</td>"
            f"<td>{html.escape(_fmt_time(incident.last_seen))}</td>"
            f"<td><details><summary>{html.escape(incident.message[:180])}</summary><pre>{context}</pre><code>{html.escape(incident.code)} · {html.escape(incident.fingerprint)}</code></details></td>"
            "</tr>"
        )
    if not incidents:
        incidents.append(
            "<tr><td colspan='8' class='empty'>選択期間に障害はありません。</td></tr>"
        )

    timeline = []
    for event in reversed(report.events[-160:]):
        context = html.escape(
            json.dumps(event.get("context") or {}, ensure_ascii=False, indent=2)
        )
        timeline.append(
            "<tr>"
            f"<td>{html.escape(_fmt_time(OperationsLoader._timestamp(event)))}</td>"
            f"<td>{html.escape(str(event.get('category')))}</td>"
            f"<td>{html.escape(str(event.get('component')))}</td>"
            f"<td>{html.escape(str(event.get('resource_id') or '-'))}</td>"
            f"<td><span class='pill event-{html.escape(str(event.get('status')))}'>{html.escape(str(event.get('status')))}</span></td>"
            f"<td><details><summary>{html.escape(str(event.get('message') or '')[:180])}</summary><pre>{context}</pre></details></td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang='ja'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VLog Operations</title>
<style>
:root{{--bg:#fbfaf7;--text:#243653;--muted:#69778f;--line:#e7e9ef;--blue:#8fb5ec;--lav:#b9a8e6;--rose:#efb4c1;--mint:#b7dbc8;--apricot:#f3cfaa;--shadow:0 18px 50px rgba(76,91,125,.09)}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(145deg,#fbfaf7,#f6f8fc 55%,#faf6fb);color:var(--text);font:14px/1.55 Inter,"Noto Sans JP",system-ui,sans-serif}}main{{max-width:1560px;margin:auto;padding:32px}}header{{display:flex;justify-content:space-between;gap:24px}}h1{{font-size:34px;margin:0}}h2{{font-size:19px}}p{{color:var(--muted)}}.state,.pill{{display:inline-flex;padding:8px 13px;border-radius:999px;font-weight:800}}.state{{background:var(--mint)}}.state.degraded{{background:var(--apricot)}}.state.critical,.pill.open,.event-failed{{background:#fde8ec;color:#9d2943}}.pill.resolved,.event-succeeded,.event-recovered{{background:#e6f4eb;color:#236a43}}.event-started{{background:#e9f1fb;color:#315f91}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}}.metric,.panel{{background:#fffffff2;border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow)}}.metric{{padding:18px}}.metric small{{display:block;color:var(--muted)}}.metric strong{{font-size:30px}}.panel{{padding:20px;margin-top:16px;overflow:hidden}}.stages{{display:grid;grid-template-columns:repeat(9,minmax(110px,1fr));gap:10px;overflow:auto}}.stage{{padding:14px;border-radius:16px;background:#f4f6fa}}.stage span,.stage small{{display:block;color:var(--muted)}}.stage strong{{font-size:24px}}.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:16px}}table{{width:100%;border-collapse:collapse;min-width:1120px;background:#fff}}th{{background:#f6f8fb;text-align:left;color:var(--muted)}}th,td{{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}}summary{{cursor:pointer;max-width:580px}}pre{{white-space:pre-wrap;background:#f7f8fb;padding:12px;border-radius:12px;max-width:680px}}code{{color:var(--muted);font-size:11px}}.empty{{text-align:center;padding:28px}}@media(max-width:900px){{main{{padding:18px}}header{{display:block}}.grid{{grid-template-columns:1fr 1fr}}}}@media(max-width:520px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><h1>VLog Operations</h1><p>障害フィンガープリントと対象リソース単位で監査するローカル運用コックピット。</p><p>生成: {_fmt_time(report.generated_at)} · 監査期間: {report.days}日</p></div><span class='state {report.state}'>{state_label}</span></header>
<section class='grid'><div class='metric'><small>実行信頼度</small><strong>{report.reliability:.1f}%</strong></div><div class='metric'><small>失敗イベント</small><strong>{report.failures}</strong></div><div class='metric'><small>未解消</small><strong>{report.open_incidents}</strong></div><div class='metric'><small>観測イベント</small><strong>{len(report.events)}</strong></div></section>
<section class='panel'><h2>パイプライン監視</h2><div class='stages'>{stages}</div></section>
<section class='panel'><h2>インシデント</h2><div class='table-wrap'><table><thead><tr><th>状態</th><th>重大度</th><th>分類</th><th>箇所</th><th>対象</th><th>回数</th><th>最終発生</th><th>詳細</th></tr></thead><tbody>{"".join(incidents)}</tbody></table></div></section>
<section class='panel'><h2>最新イベント</h2><div class='table-wrap'><table><thead><tr><th>時刻</th><th>分類</th><th>コンポーネント</th><th>対象</th><th>状態</th><th>内容</th></tr></thead><tbody>{"".join(timeline)}</tbody></table></div></section>
</main></body></html>"""


def write_report_files(
    report: OperationsReport, html_path: Path, json_path: Path
) -> None:
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_html(report), encoding="utf-8")
    json_path.write_text(
        json.dumps(report_to_dict(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_doctor(root: Path) -> int:
    state_root = runtime_directories().state
    log = OperationalEventLog(state_root / "error_events.jsonl")
    daily_text = (
        (root / "infra/systemd/vlog-daily.service.in").read_text(encoding="utf-8")
        if (root / "infra/systemd/vlog-daily.service.in").exists()
        else ""
    )
    monitor_text = (
        (root / "infra/systemd/vlog.service.in").read_text(encoding="utf-8")
        if (root / "infra/systemd/vlog.service.in").exists()
        else ""
    )
    checks = [
        (
            "uv executable",
            shutil.which("uv") is not None,
            shutil.which("uv") or "not found",
        ),
        (
            "runtime state writable",
            os.access(state_root, os.W_OK)
            if state_root.exists()
            else os.access(state_root.parent, os.W_OK),
            str(state_root),
        ),
        (
            "daily ExecStart",
            "uv run --frozen vlog-daily" in daily_text,
            "repo-relative uv daily runner",
        ),
        (
            "no stale /snap/bin/task",
            "/snap/bin/task" not in daily_text,
            "legacy scheduler path absent",
        ),
        (
            "systemd watchdog",
            "WatchdogSec=" in monitor_text and "Type=notify" in monitor_text,
            "notify watchdog enabled",
        ),
        (
            "event log retention",
            log.max_bytes > 0 and log.backups > 0 and log.retention_days > 0,
            f"{log.max_bytes} bytes / {log.backups} backups / {log.retention_days} days",
        ),
    ]
    for canonical, fallback in (
        ("VLOG_GEMINI_API_KEY", "GOOGLE_API_KEY"),
        ("VLOG_SUPABASE_URL", "SUPABASE_URL"),
        ("VLOG_SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
    ):
        configured = bool(os.environ.get(canonical) or os.environ.get(fallback))
        checks.append(
            (canonical, configured, "configured" if configured else "missing")
        )

    failed = 0
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL':4}  {name:28} {detail}")
        log.emit(
            category="scheduler"
            if "ExecStart" in name or "task" in name or "watchdog" in name
            else "infrastructure",
            component="doctor",
            operation=name.lower().replace(" ", "_"),
            status=EventStatus.SUCCEEDED if ok else EventStatus.FAILED,
            severity=Severity.INFO if ok else Severity.ERROR,
            message=f"{name}: {detail}",
            code="doctor_check",
            resource_id=name,
            retryable=False,
            context={"detail": detail},
            source="doctor",
        )
        failed += int(not ok)
    return 1 if failed else 0


def record_service_failure(unit: str, root: Path) -> int:
    context: dict[str, Any] = {"unit": unit}
    try:
        show = subprocess.run(
            [
                "systemctl",
                "--user",
                "show",
                unit,
                "-p",
                "Result",
                "-p",
                "ExecMainStatus",
                "-p",
                "ExecMainCode",
                "-p",
                "ActiveEnterTimestamp",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        context["systemctl"] = show.stdout.strip()
        journal = subprocess.run(
            [
                "journalctl",
                "--user",
                "-u",
                unit,
                "-n",
                "40",
                "--no-pager",
                "-o",
                "short-iso",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        context["journal_tail"] = journal.stdout[-12000:]
    except (OSError, subprocess.SubprocessError) as exc:
        context["collection_error"] = f"{type(exc).__name__}: {exc}"
    OperationalEventLog(runtime_directories().state / "error_events.jsonl").emit(
        category="scheduler",
        component="systemd",
        operation="service_run",
        status=EventStatus.FAILED,
        severity=Severity.CRITICAL,
        message=f"systemd unit failed: {unit}",
        code="systemd_unit_failed",
        resource_id=unit,
        retryable=True,
        context=context,
        source="systemd-onfailure",
    )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VLog operational observability")
    sub = parser.add_subparsers(dest="command")
    report = sub.add_parser("report")
    report.add_argument("--days", type=int, default=90)
    report.add_argument("--html", default="reports/operations.html")
    report.add_argument("--json", default="reports/operations.json")
    report.add_argument("--open", action="store_true")
    emit = sub.add_parser("emit")
    for name in ("category", "component", "operation", "status", "message"):
        emit.add_argument(f"--{name.replace('_', '-')}", required=True)
    emit.add_argument("--severity", default=Severity.ERROR)
    emit.add_argument("--code", default="manual_event")
    emit.add_argument("--resource-id")
    emit.add_argument("--resolves-fingerprint")
    emit.add_argument("--retryable", action="store_true")
    recover = sub.add_parser("recover-latest")
    for name in ("category", "component", "operation", "message"):
        recover.add_argument(f"--{name.replace('_', '-')}", required=True)
    recover.add_argument("--resource-id")
    recover.add_argument("--code", default="manual_recovery")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--root", default=".")
    failure = sub.add_parser("service-failure")
    failure.add_argument("--unit", required=True)
    failure.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    if not args.command:
        args.command, args.days, args.html, args.json, args.open = (
            "report",
            90,
            "reports/operations.html",
            "reports/operations.json",
            False,
        )
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "emit":
        OperationalEventLog().emit(
            category=args.category,
            component=args.component,
            operation=args.operation,
            status=args.status,
            severity=args.severity,
            code=args.code,
            message=args.message,
            resource_id=args.resource_id,
            resolves_fingerprint=args.resolves_fingerprint,
            retryable=args.retryable,
            source="cli",
        )
        return 0
    if args.command == "recover-latest":
        event = OperationalEventLog().recover_latest(
            category=args.category,
            component=args.component,
            operation=args.operation,
            resource_id=args.resource_id,
            message=args.message,
            code=args.code,
            source="cli",
        )
        if event is None:
            print("No matching open failure found.")
            return 1
        print(f"Recovered fingerprint {event['resolves_fingerprint']}")
        return 0
    if args.command == "doctor":
        return run_doctor(Path(args.root).resolve())
    if args.command == "service-failure":
        return record_service_failure(args.unit, Path(args.root).resolve())

    state_root = runtime_directories().state
    report = build_report(OperationsLoader().load(args.days), args.days)
    html_arg, json_arg = Path(args.html), Path(args.json)
    html_path = html_arg if html_arg.is_absolute() else state_root / html_arg
    json_path = json_arg if json_arg.is_absolute() else state_root / json_arg
    write_report_files(report, html_path, json_path)
    print_report(report)
    print(f"HTML: {html_path}")
    print(f"JSON: {json_path}")
    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
    return 2 if report.state == "critical" else 1 if report.state == "degraded" else 0


if __name__ == "__main__":
    raise SystemExit(main())
