from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from vlog_capture.domain.audit import AuditFinding, AuditReport, AuditState
from vlog_capture.domain.harness import IncidentType
from vlog_capture.infrastructure.settings import settings


@dataclass(frozen=True)
class ParsedRecord:
    line_no: int
    payload: dict[str, Any]


class StrictAuditor:
    def __init__(
        self,
        incident_path: Path | None = None,
        trace_path: Path | None = None,
        recent_limit: int = 100,
        trace_window_minutes: int = 30,
    ) -> None:
        self.incident_path = incident_path or settings.incident_file
        self.trace_path = trace_path or settings.trace_file
        self.recent_limit = recent_limit
        self.trace_window = timedelta(minutes=trace_window_minutes)

    def run(self) -> AuditReport:
        incidents, incident_error = self._load_jsonl(self.incident_path)
        traces, trace_error = self._load_jsonl(self.trace_path)
        findings: list[AuditFinding] = []

        findings.extend(self._audit_incident_log(incidents, incident_error))
        findings.extend(self._audit_trace_log(traces, trace_error))
        findings.extend(self._audit_task_execution(incidents, traces))
        findings.extend(self._audit_url_standardization())
        findings.extend(self._audit_adr_0010_contract())
        findings.extend(self._audit_adr_evidence())
        return AuditReport(tuple(findings))

    def _load_jsonl(self, path: Path) -> tuple[list[ParsedRecord], str | None]:
        if not path.exists():
            return [], f"missing file: {path}"

        records: list[ParsedRecord] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, raw in enumerate(handle, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    return [], f"malformed JSON at line {line_no}: {exc.msg}"
                if not isinstance(payload, dict):
                    return [], f"non-object JSON at line {line_no}"
                records.append(ParsedRecord(line_no=line_no, payload=payload))
        return records, None

    def _audit_incident_log(
        self, incidents: list[ParsedRecord], error: str | None
    ) -> list[AuditFinding]:
        if error:
            return [
                AuditFinding(
                    check_name="incident-log-integrity",
                    state=AuditState.UNVERIFIED,
                    evidence=error,
                    source=str(self.incident_path),
                )
            ]

        if not incidents:
            return [
                AuditFinding(
                    check_name="incident-log-integrity",
                    state=AuditState.UNVERIFIED,
                    evidence="no incident evidence available",
                    source=str(self.incident_path),
                )
            ]

        return [
            AuditFinding(
                check_name="incident-log-integrity",
                state=AuditState.PASS,
                evidence=self._format_incident_record(incidents[-1]),
                source=str(self.incident_path),
                metadata={"records": len(incidents)},
            )
        ]

    def _audit_trace_log(
        self, traces: list[ParsedRecord], error: str | None
    ) -> list[AuditFinding]:
        if error:
            return [
                AuditFinding(
                    check_name="trace-log-integrity",
                    state=AuditState.UNVERIFIED,
                    evidence=error,
                    source=str(self.trace_path),
                )
            ]

        if not traces:
            return [
                AuditFinding(
                    check_name="trace-log-integrity",
                    state=AuditState.UNVERIFIED,
                    evidence="no trace evidence available",
                    source=str(self.trace_path),
                )
            ]

        latest = self._latest_trace_summary(traces)
        return [
            AuditFinding(
                check_name="trace-log-integrity",
                state=AuditState.PASS,
                evidence=latest,
                source=str(self.trace_path),
                metadata={"records": len(traces)},
            )
        ]

    def _audit_task_execution(
        self, incidents: list[ParsedRecord], traces: list[ParsedRecord]
    ) -> list[AuditFinding]:
        if not incidents:
            return [
                AuditFinding(
                    check_name="task-execution",
                    state=AuditState.UNVERIFIED,
                    evidence="no incident history to audit",
                    source=str(self.incident_path),
                )
            ]

        findings: list[AuditFinding] = []
        grouped: dict[str, list[ParsedRecord]] = {}
        for record in incidents[-self.recent_limit :]:
            task_name = str(record.payload.get("task_name") or "unknown")
            grouped.setdefault(task_name, []).append(record)

        for task_name, task_records in grouped.items():
            latest = task_records[-1]
            latest_type = self._incident_type(latest.payload.get("type"))
            expected_components = self._expected_trace_components(task_name)

            if latest_type == IncidentType.FAILED:
                findings.append(
                    AuditFinding(
                        check_name=f"task:{task_name}",
                        state=AuditState.FAIL,
                        evidence=self._format_incident_record(latest),
                        details="task ended in FAILED",
                        source=str(self.incident_path),
                    )
                )
                continue

            if latest_type == IncidentType.VERIFICATION_ERROR:
                findings.append(
                    AuditFinding(
                        check_name=f"task:{task_name}",
                        state=AuditState.FAIL,
                        evidence=self._format_incident_record(latest),
                        details="task ended in VERIFICATION_ERROR",
                        source=str(self.incident_path),
                    )
                )
                continue

            if latest_type == IncidentType.TRY:
                findings.append(
                    AuditFinding(
                        check_name=f"task:{task_name}",
                        state=AuditState.UNVERIFIED,
                        evidence=self._format_incident_record(latest),
                        details="latest incident has no terminal state",
                        source=str(self.incident_path),
                    )
                )
                continue

            if latest_type == IncidentType.SKIPPED:
                findings.append(
                    AuditFinding(
                        check_name=f"task:{task_name}",
                        state=AuditState.NOT_APPLICABLE,
                        evidence=self._format_incident_record(latest),
                        details="task was intentionally skipped",
                        source=str(self.incident_path),
                    )
                )
                continue

            if latest_type != IncidentType.SUCCESS:
                findings.append(
                    AuditFinding(
                        check_name=f"task:{task_name}",
                        state=AuditState.UNVERIFIED,
                        evidence=self._format_incident_record(latest),
                        details="latest incident state is not recognized",
                        source=str(self.incident_path),
                    )
                )
                continue

            if not expected_components:
                findings.append(
                    AuditFinding(
                        check_name=f"task:{task_name}",
                        state=AuditState.NOT_APPLICABLE,
                        evidence=self._format_incident_record(latest),
                        details="no trace contract defined for this task",
                        source=str(self.incident_path),
                    )
                )
                continue

            matching_traces = self._matching_traces(traces, expected_components, latest)
            if not matching_traces:
                findings.append(
                    AuditFinding(
                        check_name=f"task:{task_name}",
                        state=AuditState.UNVERIFIED,
                        evidence=self._format_incident_record(latest),
                        details=(
                            "no trace evidence matched expected components: "
                            + ", ".join(sorted(expected_components))
                        ),
                        source=str(self.trace_path),
                    )
                )
                continue

            findings.append(
                AuditFinding(
                    check_name=f"task:{task_name}",
                    state=AuditState.PASS,
                    evidence=self._format_incident_record(latest),
                    details=self._summarize_traces(matching_traces),
                    source=str(self.trace_path),
                    metadata={"expected_components": sorted(expected_components)},
                )
            )

        return findings

    def _audit_url_standardization(self) -> list[AuditFinding]:
        relevant_files = [
            Path("README.md"),
            Path("docs/architecture.md"),
            Path("apps/reader/README.md"),
            Path("Taskfile.yaml"),
            Path(".claude/skills/discord-operations/SKILL.md"),
            Path("docs/adr/0010-external-reader-integration.md"),
        ]
        legacy_matches: list[str] = []
        current_matches: list[str] = []

        for path in relevant_files:
            if not path.exists():
                continue
            for line_no, line in self._iter_file_lines(path):
                if "rule-scribe-games.vercel.app" in line:
                    legacy_matches.append(f"{path}:{line_no}:{line.strip()}")
                if "kaflog.vercel.app" in line:
                    current_matches.append(f"{path}:{line_no}:{line.strip()}")

        if legacy_matches:
            return [
                AuditFinding(
                    check_name="url-standardization",
                    state=AuditState.FAIL,
                    evidence=legacy_matches[0],
                    details="legacy URL still present in standardized surfaces",
                    source="; ".join(legacy_matches[:3]),
                )
            ]

        if not current_matches:
            return [
                AuditFinding(
                    check_name="url-standardization",
                    state=AuditState.UNVERIFIED,
                    evidence="no standardized URL evidence found",
                    source="; ".join(str(path) for path in relevant_files),
                )
            ]

        return [
            AuditFinding(
                check_name="url-standardization",
                state=AuditState.PASS,
                evidence=current_matches[0],
                details=f"matches={len(current_matches)}",
                source="; ".join(str(path) for path in relevant_files),
                metadata={"matches": current_matches},
            )
        ]

    def _audit_adr_0010_contract(self) -> list[AuditFinding]:
        path = Path("docs/adr/0010-external-reader-integration.md")
        if not path.exists():
            return [
                AuditFinding(
                    check_name="adr-0010-contract",
                    state=AuditState.UNVERIFIED,
                    evidence=f"missing file: {path}",
                    source=str(path),
                )
            ]

        lines = [line.strip() for _, line in self._iter_file_lines(path)]
        has_taskfile_link = any("Taskfile.yaml" in line for line in lines)
        has_skill_link = any(
            ".claude/skills/discord-operations/SKILL.md" in line for line in lines
        )
        has_kaflog_url = any("https://kaflog.vercel.app" in line for line in lines)
        if not (has_taskfile_link and has_skill_link and has_kaflog_url):
            return [
                AuditFinding(
                    check_name="adr-0010-contract",
                    state=AuditState.UNVERIFIED,
                    evidence=self._format_file_excerpt(path, "kaflog.vercel.app"),
                    details="ADR contract is missing one or more required references",
                    source=str(path),
                )
            ]

        return [
            AuditFinding(
                check_name="adr-0010-contract",
                state=AuditState.PASS,
                evidence=self._format_file_excerpt(path, "kaflog.vercel.app"),
                details="Taskfile and skill references are present",
                source=str(path),
            )
        ]

    def _audit_adr_evidence(self) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        for path in sorted(Path("docs/adr").glob("*.md")):
            status = self._adr_status(path)
            if status not in {"approved", "accepted"}:
                continue

            evidence = self._adr_evidence_line(path)
            if evidence is None:
                findings.append(
                    AuditFinding(
                        check_name=f"adr-evidence:{path.stem}",
                        state=AuditState.UNVERIFIED,
                        evidence=f"missing evidence in {path}",
                        source=str(path),
                    )
                )
                continue

            findings.append(
                AuditFinding(
                    check_name=f"adr-evidence:{path.stem}",
                    state=AuditState.PASS,
                    evidence=evidence,
                    source=str(path),
                )
            )
        return findings

    def _matching_traces(
        self,
        traces: list[ParsedRecord],
        expected_components: set[str],
        incident: ParsedRecord,
    ) -> list[ParsedRecord]:
        incident_ts = self._parse_timestamp(incident.payload.get("timestamp"))
        if incident_ts is None:
            return []

        window_start = incident_ts - self.trace_window
        window_end = incident_ts + self.trace_window
        matches: list[ParsedRecord] = []
        for trace in traces:
            ts = self._parse_timestamp(trace.payload.get("timestamp"))
            if ts is None or not (window_start <= ts <= window_end):
                continue
            component = str(trace.payload.get("component") or "")
            if component in expected_components:
                matches.append(trace)
        return matches

    def _expected_trace_components(self, task_name: str) -> set[str]:
        mapping = {
            "process": {"transcriber", "summarizer", "novelizer", "image_generator"},
            "summarize": {"summarizer"},
            "novel": {"novelizer", "image_generator"},
            "transcribe": {"transcriber"},
            "image_generate": {"image_generator"},
        }
        return mapping.get(task_name, set())

    def _incident_type(self, raw_type: Any) -> IncidentType | None:
        if raw_type is None:
            return None
        try:
            return IncidentType(str(raw_type))
        except ValueError:
            return None

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _format_incident_record(self, record: ParsedRecord) -> str:
        payload = record.payload
        reason = payload.get("reason")
        ts = payload.get("timestamp", "?")
        task = payload.get("task_name", "?")
        state = payload.get("type", "?")
        reason_text = f" reason={reason}" if reason else ""
        return (
            f"{self.incident_path}:{record.line_no} "
            f"timestamp={ts} task={task} state={state}{reason_text}"
        )

    def _iter_file_lines(self, path: Path) -> Iterable[tuple[int, str]]:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                yield line_no, line

    def _format_file_excerpt(self, path: Path, needle: str) -> str:
        for line_no, line in self._iter_file_lines(path):
            if needle in line:
                return f"{path}:{line_no}:{line.strip()}"
        return f"{path}: no line matched {needle}"

    def _adr_status(self, path: Path) -> str | None:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("  status: "):
                return line.split(":", 1)[1].strip()
        return None

    def _adr_evidence_line(self, path: Path) -> str | None:
        in_frontmatter = False
        for line_no, line in self._iter_file_lines(path):
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if not in_frontmatter:
                continue
            if re.match(r"\s*- evidence:\s*\"", line):
                return f"{path}:{line_no}:{line.strip()}"
        return None

    def _latest_trace_summary(self, traces: list[ParsedRecord]) -> str:
        latest = traces[-1].payload
        component = latest.get("component", "?")
        model = latest.get("model", "?")
        ts = latest.get("timestamp", "?")
        return (
            f"{self.trace_path}:{traces[-1].line_no} timestamp={ts} "
            f"component={component} model={model}"
        )

    def _summarize_traces(self, traces: Iterable[ParsedRecord]) -> str:
        parts = []
        for trace in traces:
            payload = trace.payload
            parts.append(
                f"{trace.line_no}:{payload.get('component', '?')}@"
                f"{payload.get('timestamp', '?')}"
            )
        return "trace matches: " + ", ".join(parts)
