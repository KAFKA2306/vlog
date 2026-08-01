from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.domain.audit import AuditFinding, AuditReport, AuditState


@dataclass(frozen=True)
class Record:
    line_no: int
    payload: dict[str, Any]


class StrictRunAuditor:
    def __init__(
        self,
        run_id: str | None = None,
        run_log: Path = Path("data/daily_runs.jsonl"),
        trace_log: Path = Path("data/traces.jsonl"),
    ) -> None:
        self.run_id = run_id
        self.run_log = run_log
        self.trace_log = trace_log

    def run(self) -> AuditReport:
        run_records = self._load_jsonl(self.run_log)
        trace_records = self._load_jsonl(self.trace_log, required=False)
        selected_run_id = self.run_id or self._latest_run_id(run_records)
        findings: list[AuditFinding] = []
        if not selected_run_id:
            findings.append(
                AuditFinding(
                    "daily-run",
                    AuditState.UNVERIFIED,
                    "no run_id found",
                    source=str(self.run_log),
                )
            )
        else:
            findings.extend(
                self._audit_run(selected_run_id, run_records, trace_records)
            )
        findings.append(self._audit_sync_report(selected_run_id))
        findings.append(self._audit_rls_contract())
        return AuditReport(tuple(findings))

    def _load_jsonl(self, path: Path, required: bool = True) -> list[Record]:
        if not path.exists():
            if required:
                return []
            return []
        records: list[Record] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, start=1):
                if not raw.strip():
                    continue
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise RuntimeError(f"Non-object JSON in {path}:{line_no}")
                records.append(Record(line_no, payload))
        return records

    def _latest_run_id(self, records: list[Record]) -> str | None:
        for record in reversed(records):
            run_id = record.payload.get("run_id")
            if isinstance(run_id, str) and run_id:
                return run_id
        return None

    def _audit_run(
        self, run_id: str, records: list[Record], traces: list[Record]
    ) -> list[AuditFinding]:
        selected = [r for r in records if r.payload.get("run_id") == run_id]
        if not selected:
            return [
                AuditFinding(
                    "daily-run",
                    AuditState.UNVERIFIED,
                    f"no records for run_id={run_id}",
                    source=str(self.run_log),
                )
            ]
        grouped: dict[str, list[Record]] = {}
        for record in selected:
            task_name = str(record.payload.get("task_name") or "unknown")
            grouped.setdefault(task_name, []).append(record)
        return [
            self._audit_stage(run_id, task_name, stage_records, traces)
            for task_name, stage_records in grouped.items()
        ]

    def _audit_stage(
        self,
        run_id: str,
        task_name: str,
        records: list[Record],
        traces: list[Record],
    ) -> AuditFinding:
        started = next(
            (r for r in records if r.payload.get("status") == "try"), None
        )
        terminal = next(
            (
                r
                for r in reversed(records)
                if r.payload.get("status") in {"success", "failed", "skipped"}
            ),
            None,
        )
        if started is None or terminal is None:
            return AuditFinding(
                f"stage:{task_name}",
                AuditState.UNVERIFIED,
                f"run_id={run_id}",
                details="missing try or terminal record",
                source=str(self.run_log),
            )
        if terminal.payload.get("status") != "success":
            return AuditFinding(
                f"stage:{task_name}",
                AuditState.FAIL,
                f"{self.run_log}:{terminal.line_no}",
                details=str(terminal.payload.get("error") or "stage did not succeed"),
                source=str(self.run_log),
            )
        verification = terminal.payload.get("verification")
        if not isinstance(verification, dict) or not verification.get("verified"):
            return AuditFinding(
                f"stage:{task_name}",
                AuditState.UNVERIFIED,
                f"{self.run_log}:{terminal.line_no}",
                details="artifact verification is missing or false",
                source=str(self.run_log),
            )
        expected = set(terminal.payload.get("expected_components") or [])
        completed = set(terminal.payload.get("completed_components") or [])
        missing = expected - completed
        if missing:
            return AuditFinding(
                f"stage:{task_name}",
                AuditState.FAIL,
                f"{self.run_log}:{terminal.line_no}",
                details="missing completed components: " + ", ".join(sorted(missing)),
                source=str(self.run_log),
            )

        ai_components = expected & {"summarizer", "novelizer", "image_generator"}
        if ai_components:
            actual_traces = self._correlated_trace_components(
                run_id, task_name, started, terminal, traces
            )
            missing_traces = ai_components - actual_traces
            if missing_traces:
                return AuditFinding(
                    f"stage:{task_name}",
                    AuditState.UNVERIFIED,
                    f"{self.trace_log}",
                    details="missing correlated traces: "
                    + ", ".join(sorted(missing_traces)),
                    source=str(self.trace_log),
                )
        return AuditFinding(
            f"stage:{task_name}",
            AuditState.PASS,
            f"{self.run_log}:{terminal.line_no}",
            details=f"run_id={run_id}; components and artifacts verified",
            source=str(self.run_log),
            metadata={"verification": verification},
        )

    def _correlated_trace_components(
        self,
        run_id: str,
        task_name: str,
        started: Record,
        terminal: Record,
        traces: list[Record],
    ) -> set[str]:
        start_ts = self._parse_time(started.payload.get("timestamp"))
        end_ts = self._parse_time(terminal.payload.get("timestamp"))
        if start_ts is None or end_ts is None:
            return set()
        return {
            str(trace.payload.get("component"))
            for trace in traces
            if trace.payload.get("run_id") == run_id
            and trace.payload.get("task_name") == task_name
            and (ts := self._parse_time(trace.payload.get("timestamp"))) is not None
            and start_ts <= ts <= end_ts
        }

    def _audit_sync_report(self, run_id: str | None) -> AuditFinding:
        if not run_id:
            return AuditFinding(
                "sync-report", AuditState.UNVERIFIED, "run_id unavailable"
            )
        path = Path("data/sync_reports") / f"{run_id}.json"
        if not path.exists():
            return AuditFinding(
                "sync-report",
                AuditState.UNVERIFIED,
                f"missing file: {path}",
                source=str(path),
            )
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("run_id") != run_id or not report.get("verified"):
            return AuditFinding(
                "sync-report",
                AuditState.FAIL,
                str(path),
                details="sync report is not verified for this run",
                source=str(path),
            )
        if int(report.get("total", 0)) <= 0:
            return AuditFinding(
                "sync-report",
                AuditState.FAIL,
                str(path),
                details="database reflection count is zero",
                source=str(path),
            )
        return AuditFinding(
            "sync-report",
            AuditState.PASS,
            str(path),
            details=f"verified rows={report['total']}",
            source=str(path),
        )

    def _audit_rls_contract(self) -> AuditFinding:
        path = Path("supabase/schema.sql")
        if not path.exists():
            return AuditFinding(
                "rls-contract",
                AuditState.UNVERIFIED,
                f"missing file: {path}",
                source=str(path),
            )
        sql = path.read_text(encoding="utf-8").lower()
        dangerous = re.search(r"for\s+all\s+using\s*\(\s*true\s*\)", sql)
        secure = (
            "to anon, authenticated" in sql
            and "using (is_public = true)" in sql
            and "grant select on table public.daily_entries" in sql
            and "grant select on table public.novels" in sql
        )
        if dangerous or not secure:
            return AuditFinding(
                "rls-contract",
                AuditState.FAIL,
                str(path),
                details="anonymous roles are not constrained to public SELECT",
                source=str(path),
            )
        return AuditFinding(
            "rls-contract",
            AuditState.PASS,
            str(path),
            details="anonymous roles are public-row SELECT-only",
            source=str(path),
        )

    def _parse_time(self, value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
