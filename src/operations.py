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

from src.infrastructure.observability import (
    EventStatus,
    OperationalEventLog,
    Severity,
    make_fingerprint,
    sanitize,
)

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
STATUS_SUCCESS = {"succeeded", "recovered"}
STATUS_FAILURE = {"failed"}


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
        return (self.successes / total * 100.0) if total else 100.0

    @property
    def open_incidents(self) -> int:
        return sum(1 for incident in self.incidents if incident.is_open)

    @property
    def state(self) -> str:
        if any(i.is_open and i.severity == "critical" for i in self.incidents):
            return "critical"
        if self.open_incidents or self.reliability < 95:
            return "degraded"
        return "healthy"


class OperationsLoader:
    def __init__(self, root: Path = Path.cwd()) -> None:
        self.root = root.resolve()

    def load(self, days: int) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        events: list[dict[str, Any]] = []
        event_path = self.root / "data/error_events.jsonl"
        rotated = sorted(
            event_path.parent.glob(event_path.name + ".*"),
            key=self._rotation_index,
            reverse=True,
        )
        for path in rotated:
            if path.suffix == ".lock":
                continue
            events.extend(self._load_jsonl(path))
        events.extend(self._load_jsonl(event_path))
        events.extend(self._load_incidents(self.root / "data/incidents.jsonl"))
        events.extend(self._load_daily_runs(self.root / "data/daily_runs.jsonl"))
        events.extend(self._load_legacy_log(self.root / "data/logs/vlog.log"))
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
        if not path.exists() or not path.is_file():
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
                        "status": "failed",
                        "severity_text": "warning",
                        "code": "invalid_jsonl",
                        "message": f"Invalid JSONL at {path.name}:{line_no}",
                        "context": {"line": raw[:160]},
                        "source": str(path),
                        "resource_id": path.name,
                    }
                events.append(self._canonical(payload, source=str(path)))
        return events

    def _load_incidents(self, path: Path) -> list[dict[str, Any]]:
        events = self._load_jsonl(path)
        for event in events:
            if event.get("status") in {"open", "active", "error"}:
                event["status"] = "failed"
            elif event.get("status") in {"closed", "resolved"}:
                event["status"] = "recovered"
                event.setdefault("resolves_fingerprint", event.get("fingerprint"))
        return events

    def _load_daily_runs(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
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
                "try": "started",
                "success": "succeeded",
                "failed": "failed",
            }.get(str(payload.get("status")), str(payload.get("status") or "started"))
            error = payload.get("error")
            events.append(
                self._canonical(
                    {
                        "timestamp": payload.get("timestamp"),
                        "category": category,
                        "component": "daily-pipeline",
                        "operation": task,
                        "status": status,
                        "severity_text": "error" if status == "failed" else "info",
                        "code": f"daily_{prefix}_{status}",
                        "message": str(error or f"Daily stage {task}: {status}"),
                        "run_id": payload.get("run_id"),
                        "resource_id": task,
                        "context": {
                            "expected_components": payload.get("expected_components"),
                            "verification": payload.get("verification"),
                        },
                        "source": str(path),
                    },
                    source=str(path),
                )
            )
        return events

    def _load_legacy_log(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
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
                    "error"
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
                    else "warning"
                )
                events.append(
                    self._canonical(
                        {
                            "timestamp": timestamp,
                            "category": category,
                            "component": component,
                            "operation": operation,
                            "status": "failed",
                            "severity_text": severity,
                            "code": code,
                            "message": raw.strip()[:800],
                            "context": {"line_no": line_no},
                            "source": str(path),
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
        event.setdefault("status", "failed")
        event.setdefault("severity_text", event.get("severity", "error"))
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
    resolved_fingerprints = {
        str(event.get("resolves_fingerprint"))
        for event in events
        if event.get("status") == EventStatus.RECOVERED
        and event.get("resolves_fingerprint")
    }
    for event in events:
        if event.get("status") not in STATUS_FAILURE:
            continue
        fingerprint = str(event.get("fingerprint") or "")
        resource_id = (
            str(event.get("resource_id"))
            if event.get("resource_id") is not None
            else None
        )
        failures_by_key[(fingerprint, resource_id)].append(event)

    incidents: list[Incident] = []
    for key, failures in failures_by_key.items():
        failures.sort(key=OperationsLoader._timestamp)
        first_failure = failures[0]
        last_failure = failures[-1]
        severity = max(
            (
                str(
                    event.get("severity_text")
                    or event.get("severity")
                    or "error"
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
                is_open=fingerprint not in resolved_fingerprints,
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
        f"reliability={report.reliability:.1f}%  failures={report.failures}  "
        f"open_incidents={report.open_incidents}  events={len(report.events)}"
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
            f"{state_text:8} {incident.severity.upper():8} {incident.count:5d} "
            f"{_fmt_time(incident.last_seen):16} "
            f"{(incident.resource_id or '-'):18.18} {issue[:100]}"
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
    max_count = max(category_counts.values(), default=1)
    state_label = {"healthy": "正常", "degraded": "要確認", "critical": "重大障害"}[
        report.state
    ]

    stage_cards = []
    for category in CATEGORY_ORDER:
        total = category_counts.get(category, 0)
        failed = category_failures.get(category, 0)
        stage_state = "critical" if failed else ("quiet" if total == 0 else "healthy")
        stage_cards.append(
            f"<div class='stage {stage_state}'><span>{html.escape(category)}</span>"
            f"<strong>{failed}</strong><small>fail / {total} events</small></div>"
        )

    incident_rows = []
    for incident in report.incidents[:80]:
        state = "未解消" if incident.is_open else "解消済み"
        context = html.escape(
            json.dumps(incident.context, ensure_ascii=False, indent=2)
        )
        resource = html.escape(incident.resource_id or "-")
        incident_rows.append(
            "<tr>"
            f"<td><span class='pill {'open' if incident.is_open else 'resolved'}'>{state}</span></td>"
            f"<td><span class='severity {html.escape(incident.severity)}'>{html.escape(incident.severity)}</span></td>"
            f"<td>{html.escape(incident.category)}</td>"
            f"<td><strong>{html.escape(incident.component)}</strong><br><small>{html.escape(incident.operation)}</small></td>"
            f"<td><code>{resource}</code></td>"
            f"<td class='count'>{incident.count}</td>"
            f"<td>{html.escape(_fmt_time(incident.last_seen))}</td>"
            f"<td><details><summary>{html.escape(incident.message[:180])}</summary><pre>{context}</pre>"
            f"<code>{html.escape(incident.code)} · {html.escape(incident.fingerprint)}</code></details></td>"
            "</tr>"
        )
    if not incident_rows:
        incident_rows.append(
            "<tr><td colspan='8' class='empty'>選択期間に障害はありません。</td></tr>"
        )

    timeline_rows = []
    for event in reversed(report.events[-160:]):
        timestamp = OperationsLoader._timestamp(event)
        context = html.escape(
            json.dumps(event.get("context") or {}, ensure_ascii=False, indent=2)
        )
        timeline_rows.append(
            "<tr>"
            f"<td>{html.escape(_fmt_time(timestamp))}</td>"
            f"<td>{html.escape(str(event.get('category')))}</td>"
            f"<td>{html.escape(str(event.get('component')))}</td>"
            f"<td>{html.escape(str(event.get('resource_id') or '-'))}</td>"
            f"<td><span class='pill event-{html.escape(str(event.get('status')))}'>{html.escape(str(event.get('status')))}</span></td>"
            f"<td><details><summary>{html.escape(str(event.get('message') or '')[:180])}</summary><pre>{context}</pre></details></td>"
            "</tr>"
        )
    if not timeline_rows:
        timeline_rows.append(
            "<tr><td colspan='6' class='empty'>イベントがありません。</td></tr>"
        )

    bars = []
    for category in CATEGORY_ORDER:
        total = category_counts.get(category, 0)
        failed = category_failures.get(category, 0)
        width = int(total / max_count * 100) if total else 0
        bars.append(
            "<div class='bar-row'>"
            f"<span>{html.escape(category)}</span>"
            f"<div class='bar-track'><i style='width:{width}%'></i></div>"
            f"<b>{total}</b><em>{failed} fail</em></div>"
        )

    return f"""<!doctype html>
<html lang='ja'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>VLog Operations</title>
<style>
:root{{--bg:#fbfaf7;--surface:#fff;--text:#243653;--muted:#69778f;--line:#e7e9ef;--blue:#8fb5ec;--lav:#b9a8e6;--rose:#efb4c1;--mint:#b7dbc8;--apricot:#f3cfaa;--shadow:0 18px 50px rgba(76,91,125,.09)}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(145deg,#fbfaf7 0%,#f6f8fc 55%,#faf6fb 100%);color:var(--text);font:14px/1.55 Inter,"Noto Sans JP",system-ui,sans-serif}}
main{{max-width:1560px;margin:auto;padding:32px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:24px}}h1{{font-size:34px;margin:0;letter-spacing:-.04em}}h2{{margin:0 0 14px;font-size:19px}}p{{margin:4px 0;color:var(--muted)}}.state{{padding:10px 16px;border-radius:999px;font-weight:800;background:var(--mint)}}.state.degraded{{background:var(--apricot)}}.state.critical{{background:var(--rose)}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:16px}}.metric,.panel{{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow)}}.metric{{padding:18px}}.metric small{{display:block;color:var(--muted);font-weight:700}}.metric strong{{display:block;font-size:30px;letter-spacing:-.04em;margin-top:5px}}.metric:nth-child(1){{border-top:5px solid var(--mint)}}.metric:nth-child(2){{border-top:5px solid var(--rose)}}.metric:nth-child(3){{border-top:5px solid var(--apricot)}}.metric:nth-child(4){{border-top:5px solid var(--blue)}}
.panel{{padding:20px;margin-top:16px;overflow:hidden}}.stages{{display:grid;grid-template-columns:repeat(9,minmax(110px,1fr));gap:10px;overflow:auto;padding-bottom:4px}}.stage{{padding:14px;border-radius:16px;background:#f4f6fa;border:1px solid var(--line);min-width:120px}}.stage span,.stage small{{display:block;color:var(--muted)}}.stage strong{{font-size:24px}}.stage.healthy{{background:#f2faf6;border-color:#d8eee2}}.stage.critical{{background:#fff4f6;border-color:#f4d4da}}.stage.quiet{{opacity:.65}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:16px}}table{{width:100%;border-collapse:collapse;min-width:1120px;background:#fff}}th{{position:sticky;top:0;background:#f6f8fb;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}th,td{{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}}tbody tr:hover{{background:#fbfcff}}.count{{font-size:18px;font-weight:800}}.pill,.severity{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:11px;font-weight:800;text-transform:uppercase}}.pill.open,.event-failed,.severity.critical,.severity.error{{background:#fde8ec;color:#9d2943}}.pill.resolved,.event-succeeded,.event-recovered{{background:#e6f4eb;color:#236a43}}.event-started,.event-heartbeat{{background:#e9f1fb;color:#315f91}}.event-skipped,.severity.warning{{background:#fff0d8;color:#8a5a16}}.severity.info{{background:#eef0f5;color:#536078}}
summary{{cursor:pointer;max-width:580px}}pre{{white-space:pre-wrap;background:#f7f8fb;padding:12px;border-radius:12px;max-width:680px;overflow:auto}}code{{display:block;margin-top:7px;color:var(--muted);font-size:11px}}.empty{{text-align:center;padding:28px;color:var(--muted)}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.bar-row{{display:grid;grid-template-columns:110px 1fr 42px 64px;gap:10px;align-items:center;margin:10px 0}}.bar-track{{height:10px;background:#edf0f5;border-radius:999px;overflow:hidden}}.bar-track i{{display:block;height:100%;background:linear-gradient(90deg,var(--blue),var(--lav));border-radius:999px}}.bar-row em{{font-style:normal;color:var(--muted);font-size:12px}}footer{{padding:28px 4px;color:var(--muted)}}
@media(max-width:900px){{main{{padding:18px}}header{{display:block}}.state{{display:inline-flex;margin-top:12px}}.grid{{grid-template-columns:1fr 1fr}}.two{{grid-template-columns:1fr}}}}@media(max-width:520px){{.grid{{grid-template-columns:1fr}}h1{{font-size:28px}}}}
</style></head>
<body><main>
<header><div><h1>VLog Operations</h1><p>録音から同期・通知までを、障害フィンガープリントと対象リソース単位で監査するローカル運用コックピット。</p><p>生成: {html.escape(_fmt_time(report.generated_at))} · 監査期間: {report.days}日</p></div><span class='state {report.state}'>{state_label}</span></header>
<section class='grid'><div class='metric'><small>実行信頼度</small><strong>{report.reliability:.1f}%</strong></div><div class='metric'><small>失敗イベント</small><strong>{report.failures}</strong></div><div class='metric'><small>未解消インシデント</small><strong>{report.open_incidents}</strong></div><div class='metric'><small>観測イベント</small><strong>{len(report.events)}</strong></div></section>
<section class='panel'><h2>パイプライン監視</h2><div class='stages'>{"".join(stage_cards)}</div></section>
<section class='panel'><h2>対応が必要な障害</h2><div class='table-wrap'><table><thead><tr><th>状態</th><th>重大度</th><th>分類</th><th>箇所</th><th>対象</th><th>回数</th><th>最終発生</th><th>詳細</th></tr></thead><tbody>{"".join(incident_rows)}</tbody></table></div></section>
<section class='two'><div class='panel'><h2>カテゴリ別イベント量</h2>{"".join(bars)}</div><div class='panel'><h2>運用原則</h2><p><strong>通常の成功では障害を閉じません。</strong></p><p>同じフィンガープリントを明示的に参照する recovered イベントだけが解消の証跡になります。</p><p>ログはプロセス間排他、サイズローテーション、90日保持、秘密値マスクを適用します。</p><p>systemd watchdogとWindows側監視を併用し、WSL内外の停止を分離して検知します。</p></div></section>
<section class='panel'><h2>最新イベント</h2><div class='table-wrap'><table><thead><tr><th>時刻</th><th>分類</th><th>コンポーネント</th><th>対象</th><th>状態</th><th>内容</th></tr></thead><tbody>{"".join(timeline_rows)}</tbody></table></div></section>
<footer>VLog Operations · local-only report · raw logs are not published.</footer>
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
    log = OperationalEventLog(root / "data/error_events.jsonl")
    checks: list[tuple[str, bool, str]] = []
    uv_path = shutil.which("uv")
    checks.append(("uv executable", uv_path is not None, uv_path or "not found"))
    checks.append(
        (
            "project data writable",
            os.access(root / "data", os.W_OK)
            if (root / "data").exists()
            else os.access(root, os.W_OK),
            str(root / "data"),
        )
    )
    for key in ("GOOGLE_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        checks.append(
            (
                key,
                bool(os.environ.get(key)),
                "configured" if os.environ.get(key) else "missing",
            )
        )
    daily_path = root / "vlog-daily.service"
    monitor_path = root / "vlog.service"
    daily_text = daily_path.read_text(encoding="utf-8") if daily_path.exists() else ""
    monitor_text = (
        monitor_path.read_text(encoding="utf-8") if monitor_path.exists() else ""
    )
    checks.extend(
        [
            (
                "daily ExecStart",
                "uv run python -m src.daily" in daily_text,
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
                f"{log.max_bytes} bytes / {log.backups} backups / "
                f"{log.retention_days} days",
            ),
        ]
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
        if not ok:
            failed += 1
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
    OperationalEventLog(root / "data/error_events.jsonl").emit(
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

    report_parser = sub.add_parser(
        "report", help="Build console, JSON and HTML reports"
    )
    report_parser.add_argument("--days", type=int, default=90)
    report_parser.add_argument("--html", default="data/reports/operations.html")
    report_parser.add_argument("--json", default="data/reports/operations.json")
    report_parser.add_argument("--open", action="store_true")

    emit_parser = sub.add_parser("emit", help="Append one structured event")
    emit_parser.add_argument("--category", required=True)
    emit_parser.add_argument("--component", required=True)
    emit_parser.add_argument("--operation", required=True)
    emit_parser.add_argument("--status", required=True)
    emit_parser.add_argument("--severity", default="error")
    emit_parser.add_argument("--code", default="manual_event")
    emit_parser.add_argument("--message", required=True)
    emit_parser.add_argument("--resource-id")
    emit_parser.add_argument("--resolves-fingerprint")
    emit_parser.add_argument("--retryable", action="store_true")

    recover_parser = sub.add_parser(
        "recover-latest", help="Explicitly recover the latest matching open failure"
    )
    recover_parser.add_argument("--category", required=True)
    recover_parser.add_argument("--component", required=True)
    recover_parser.add_argument("--operation", required=True)
    recover_parser.add_argument("--resource-id")
    recover_parser.add_argument("--code", default="manual_recovery")
    recover_parser.add_argument("--message", required=True)

    doctor_parser = sub.add_parser(
        "doctor", help="Validate operational prerequisites"
    )
    doctor_parser.add_argument("--root", default=".")

    failure_parser = sub.add_parser(
        "service-failure", help="Capture a failed systemd unit"
    )
    failure_parser.add_argument("--unit", required=True)
    failure_parser.add_argument("--root", default=".")

    args = parser.parse_args(argv)
    if not args.command:
        args.command = "report"
        args.days = 90
        args.html = "data/reports/operations.html"
        args.json = "data/reports/operations.json"
        args.open = False
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

    root = Path.cwd()
    report = build_report(OperationsLoader(root).load(args.days), args.days)
    html_path = root / args.html
    json_path = root / args.json
    write_report_files(report, html_path, json_path)
    print_report(report)
    print(f"HTML: {html_path}")
    print(f"JSON: {json_path}")
    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
    return 2 if report.state == "critical" else (1 if report.state == "degraded" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
