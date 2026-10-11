from datetime import date
from pathlib import Path

import pytest
from vlog_capture.daily import DailyPipeline


def test_failure_prevents_success_notification(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []

    def runner(command, env, cwd):
        calls.append((list(command), dict(env), cwd))
        if "vrcpet-ingest" in command:
            run_id = env["VLOG_RUN_ID"]
            artifact = tmp_path / "data/vrcpet/runs" / f"{run_id}.json"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("{}", encoding="utf-8")
        if "sync" in command:
            raise RuntimeError("sync failed")

    pipeline = DailyPipeline(
        runner=runner,
        monitor=lambda: False,
        project_root=tmp_path,
    )
    with pytest.raises(RuntimeError, match="sync failed"):
        pipeline.run()
    assert not any("notify" in command for command, _, _ in calls)


def test_success_notification_runs_after_audit(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []

    def runner(command, env, cwd):
        calls.append((list(command), dict(env), cwd))
        if "vrcpet-ingest" in command:
            run_id = env["VLOG_RUN_ID"]
            artifact = tmp_path / "data/vrcpet/runs" / f"{run_id}.json"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("{}", encoding="utf-8")
        if "sync" in command:
            run_id = env["VLOG_RUN_ID"]
            report = tmp_path / "data/sync_reports" / f"{run_id}.json"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("{}", encoding="utf-8")

    run_id = DailyPipeline(
        runner=runner, monitor=lambda: False, project_root=tmp_path
    ).run()
    commands = [command for command, _, _ in calls]
    audit_index = next(i for i, command in enumerate(commands) if "audit" in command)
    notify_index = next(i for i, command in enumerate(commands) if "notify" in command)
    assert audit_index < notify_index
    assert run_id
    assert calls[notify_index][1]["VLOG_DAILY_VERIFIED"] == "1"


def test_daily_run_quarantines_unusable_recordings(tmp_path: Path) -> None:
    recordings = tmp_path / "data/recordings"
    recordings.mkdir(parents=True)
    bad_recording = recordings / f"{date.today():%Y%m%d}_broken.flac"
    bad_recording.write_bytes(b"")

    def runner(command, env, cwd):
        run_id = env["VLOG_RUN_ID"]
        if "sync" in command:
            report = tmp_path / "data/sync_reports" / f"{run_id}.json"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("{}", encoding="utf-8")
        vrcpet = tmp_path / "data/vrcpet/runs" / f"{run_id}.json"
        vrcpet.parent.mkdir(parents=True, exist_ok=True)
        vrcpet.write_text("{}", encoding="utf-8")

    DailyPipeline(runner=runner, monitor=lambda: False, project_root=tmp_path).run()

    assert not bad_recording.exists()
    assert (tmp_path / "data/archives/quarantine" / bad_recording.name).exists()


def test_comedy_stage_runs_independently_and_fails_on_missing_artifact(
    tmp_path: Path,
) -> None:
    today = f"{date.today():%Y%m%d}"
    summary = tmp_path / "data/summaries" / f"{today}_summary.txt"
    summary.parent.mkdir(parents=True)
    summary.write_text("summary", encoding="utf-8")
    calls: list[list[str]] = []

    def runner(command, env, cwd):
        calls.append(list(command))
        run_id = env["VLOG_RUN_ID"]
        vrcpet = tmp_path / "data/vrcpet/runs" / f"{run_id}.json"
        vrcpet.parent.mkdir(parents=True, exist_ok=True)
        vrcpet.write_text("{}", encoding="utf-8")
        if "novel" in command:
            for rel in (f"novels/{today}.md", f"photos/{today}.png"):
                path = tmp_path / "data" / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Missing stage artifacts"):
        DailyPipeline(runner=runner, monitor=lambda: False, project_root=tmp_path).run()

    novel_index = next(i for i, c in enumerate(calls) if "novel" in c)
    comedy_index = next(i for i, c in enumerate(calls) if "comedy" in c)
    assert novel_index < comedy_index
    assert ["--date", today] == calls[comedy_index][-2:]
