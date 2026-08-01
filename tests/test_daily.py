from pathlib import Path

import pytest

from src.daily import DailyPipeline


def test_failure_prevents_success_notification(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []

    def runner(command, env, cwd):
        calls.append((list(command), dict(env), cwd))
        if "sync" in command:
            raise RuntimeError("sync failed")

    pipeline = DailyPipeline(runner=runner, monitor=lambda: False, project_root=tmp_path)
    with pytest.raises(RuntimeError, match="sync failed"):
        pipeline.run()
    assert not any("notify" in command for command, _, _ in calls)


def test_success_notification_runs_after_audit(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, str], Path]] = []

    def runner(command, env, cwd):
        calls.append((list(command), dict(env), cwd))
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
