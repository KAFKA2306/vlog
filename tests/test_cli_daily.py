from types import SimpleNamespace

from vlog_capture import cli_handlers


def test_cmd_daily_uses_canonical_pipeline(monkeypatch) -> None:
    calls: list[str] = []

    class StubPipeline:
        def run(self) -> None:
            calls.append("run")

    monkeypatch.setattr("vlog_capture.daily.DailyPipeline", StubPipeline)
    cli_handlers.cmd_daily(SimpleNamespace())
    assert calls == ["run"]
