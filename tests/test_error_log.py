from datetime import datetime, timedelta

from src.domain.error_events import ErrorEvent, ErrorKind, ErrorStage, event_for_failure
from src.infrastructure.error_log import ErrorLogRepository


def test_error_event_classifies_sync_failure() -> None:
    event = event_for_failure("sync", "connection failed")

    assert event.stage is ErrorStage.SYNC
    assert event.kind is ErrorKind.SYNC_FAILED


def test_error_log_returns_events_within_requested_window(tmp_path) -> None:
    repository = ErrorLogRepository(tmp_path / "errors.jsonl")
    old_event = ErrorEvent(
        timestamp=datetime.now() - timedelta(days=31),
        stage=ErrorStage.PROCESSING,
        kind=ErrorKind.PROCESSING_FAILED,
        task_name="process",
        reason="old failure",
    )
    recent_event = ErrorEvent(
        timestamp=datetime.now(),
        stage=ErrorStage.RECORDING,
        kind=ErrorKind.RECORDING_EMPTY,
        task_name="recording_stop",
        reason="empty recording",
    )

    repository.append(old_event)
    repository.append(recent_event)

    assert repository.recent(30) == [recent_event]
