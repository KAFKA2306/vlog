import json
from pathlib import Path

from src.domain.audit import AuditState
from src.infrastructure.audit_v2 import StrictRunAuditor


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def prepare_contract(tmp_path: Path, monkeypatch, run_id: str) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "infra/supabase").mkdir(parents=True)
    (tmp_path / "infra/supabase/schema.sql").write_text(
        "revoke all on table public.daily_entries "
        "from public, anon, authenticated;\n"
        "grant select on table public.daily_entries to anon, authenticated;\n"
        "grant select on table public.novels to anon, authenticated;\n"
        "create policy p on daily_entries for select to anon, authenticated "
        "using (is_public = true);",
        encoding="utf-8",
    )
    report_dir = tmp_path / "data/sync_reports"
    report_dir.mkdir(parents=True)
    (report_dir / f"{run_id}.json").write_text(
        json.dumps({"run_id": run_id, "verified": True, "total": 2}),
        encoding="utf-8",
    )


def test_correlated_complete_stage_passes(tmp_path: Path, monkeypatch) -> None:
    run_id = "run-1"
    prepare_contract(tmp_path, monkeypatch, run_id)
    run_log = tmp_path / "data/daily_runs.jsonl"
    trace_log = tmp_path / "data/traces.jsonl"
    write_jsonl(
        run_log,
        [
            {
                "timestamp": "2026-08-02T07:00:00",
                "run_id": run_id,
                "task_name": "summarize:20260801",
                "status": "try",
            },
            {
                "timestamp": "2026-08-02T07:00:02",
                "run_id": run_id,
                "task_name": "summarize:20260801",
                "status": "success",
                "expected_components": ["summarizer"],
                "completed_components": ["summarizer"],
                "verification": {"verified": True},
            },
        ],
    )
    write_jsonl(
        trace_log,
        [
            {
                "timestamp": "2026-08-02T07:00:01",
                "run_id": run_id,
                "task_name": "summarize:20260801",
                "component": "summarizer",
            }
        ],
    )
    report = StrictRunAuditor(run_id, run_log, trace_log).run()
    stage = next(f for f in report.findings if f.check_name.startswith("stage:"))
    assert stage.state is AuditState.PASS
    assert not report.has_blockers


def test_unrelated_trace_does_not_pass(tmp_path: Path, monkeypatch) -> None:
    run_id = "run-2"
    prepare_contract(tmp_path, monkeypatch, run_id)
    run_log = tmp_path / "data/daily_runs.jsonl"
    trace_log = tmp_path / "data/traces.jsonl"
    write_jsonl(
        run_log,
        [
            {
                "timestamp": "2026-08-02T07:00:00",
                "run_id": run_id,
                "task_name": "novel:20260801",
                "status": "try",
            },
            {
                "timestamp": "2026-08-02T07:00:03",
                "run_id": run_id,
                "task_name": "novel:20260801",
                "status": "success",
                "expected_components": ["novelizer", "image_generator"],
                "completed_components": ["novelizer", "image_generator"],
                "verification": {"verified": True},
            },
        ],
    )
    write_jsonl(
        trace_log,
        [
            {
                "timestamp": "2026-08-02T07:00:01",
                "run_id": "other-run",
                "task_name": "novel:20260801",
                "component": "image_generator",
            },
            {
                "timestamp": "2026-08-02T07:00:02",
                "run_id": run_id,
                "task_name": "novel:20260801",
                "component": "novelizer",
            },
        ],
    )
    report = StrictRunAuditor(run_id, run_log, trace_log).run()
    stage = next(f for f in report.findings if f.check_name.startswith("stage:"))
    assert stage.state is AuditState.UNVERIFIED
    assert "image_generator" in (stage.details or "")
