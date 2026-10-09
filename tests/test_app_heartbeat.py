import logging
from unittest.mock import Mock

from vlog_capture.app import Application


def _heartbeat_app() -> Application:
    app = Application.__new__(Application)
    app._last_heartbeat_at = -30.0
    app._last_heartbeat_log_at = -300.0
    app._last_heartbeat_log_state = None
    app._events = Mock()
    app._recorder = Mock()
    app._recorder.is_recording = False
    app._active_file = None
    app._processing_threads = set()
    return app


def test_waiting_heartbeat_is_logged_immediately_and_periodically(
    monkeypatch, caplog
) -> None:
    app = _heartbeat_app()
    current_time = 1.0
    monkeypatch.setattr("vlog_capture.app.time.monotonic", lambda: current_time)

    with caplog.at_level(logging.INFO, logger="vlog_capture.app"):
        app._heartbeat("healthy", vrchat_running=False)
        current_time = 20.0
        app._heartbeat("healthy", vrchat_running=False)
        current_time = 331.0
        app._heartbeat("healthy", vrchat_running=False)

    messages = [record.getMessage() for record in caplog.records]
    assert messages == [
        "Monitor waiting: VRChat process not detected; recording=False; workers=0",
        "Monitor waiting: VRChat process not detected; recording=False; workers=0",
    ]


def test_heartbeat_logs_immediately_when_vrchat_state_changes(
    monkeypatch, caplog
) -> None:
    app = _heartbeat_app()
    current_time = 1.0
    monkeypatch.setattr("vlog_capture.app.time.monotonic", lambda: current_time)

    with caplog.at_level(logging.INFO, logger="vlog_capture.app"):
        app._heartbeat("healthy", vrchat_running=False)
        current_time = 31.0
        app._heartbeat("healthy", vrchat_running=True)

    assert [record.getMessage() for record in caplog.records] == [
        "Monitor waiting: VRChat process not detected; recording=False; workers=0",
        "Monitor heartbeat: VRChat detected; recording=False; workers=0",
    ]
