from types import SimpleNamespace

from vlog_capture import cli_handlers


class StubEvaluator:
    executed_dates: list[str] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    def execute(self, date_str: str, sync: bool = True):
        self.executed_dates.append(date_str)
        return {"date": date_str}


def _patch_daily(monkeypatch, *, recordings_pending: int, autorun: bool):
    StubEvaluator.executed_dates = []
    plan = SimpleNamespace(
        counts=SimpleNamespace(
            recordings_pending=recordings_pending, novel_days_pending=1
        ),
        can_autorun_recording_flow=autorun,
        next_action_limit=1,
    )
    harness_calls: list[tuple[str, object]] = []

    monkeypatch.setattr(cli_handlers, "collect_daily_workload", lambda: plan)
    monkeypatch.setattr(cli_handlers, "render_daily_workload", lambda _plan: "plan")
    monkeypatch.setattr(
        cli_handlers,
        "_harness_run",
        lambda task_name, weight, func, *args, **kwargs: harness_calls.append(
            (task_name, weight)
        ),
    )
    monkeypatch.setattr(
        "vlog_capture.use_cases.evaluate.EvaluateDailyContentUseCase", StubEvaluator
    )
    monkeypatch.setattr(
        cli_handlers,
        "_collect_pending_evaluation_dates",
        lambda limit=None: ["20260620"],
    )
    monkeypatch.setattr(cli_handlers, "_run_daily_postprocessing", lambda: None)
    return harness_calls


def test_cmd_daily_skips_recording_flow_when_resources_busy(monkeypatch, capsys):
    harness_calls = _patch_daily(monkeypatch, recordings_pending=1, autorun=False)

    cli_handlers._cmd_daily_logic(SimpleNamespace())

    captured = capsys.readouterr().out
    assert "recording_flow=paused waiting for VRChat/GPU/CPU headroom" in captured
    assert harness_calls == []
    assert StubEvaluator.executed_dates == ["20260620"]


def test_cmd_daily_runs_recording_flow_when_resources_are_idle(monkeypatch):
    harness_calls = _patch_daily(monkeypatch, recordings_pending=1, autorun=True)

    cli_handlers._cmd_daily_logic(SimpleNamespace())

    assert harness_calls == [("daily_recording_flow", cli_handlers.TaskWeight.HEAVY)]
    assert StubEvaluator.executed_dates == ["20260620"]


def test_run_daily_postprocessing_runs_all_steps(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(
        cli_handlers, "_run_cognee_ingest", lambda: calls.append("ingest")
    )

    class StubRepo:
        def sync(self) -> None:
            calls.append("sync")

    monkeypatch.setattr(cli_handlers, "SupabaseRepository", StubRepo)
    monkeypatch.setattr(
        cli_handlers, "_send_daily_notification", lambda: calls.append("notify")
    )

    cli_handlers._run_daily_postprocessing()

    assert calls == ["ingest", "sync", "notify"]
