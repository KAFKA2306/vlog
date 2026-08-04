from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ErrorStage(StrEnum):
    RECORDING = "recording"
    PROCESSING = "processing"
    SYNC = "sync"
    SCHEDULER = "scheduler"


class ErrorKind(StrEnum):
    RECORDING_START_FAILED = "recording_start_failed"
    RECORDING_STOP_FAILED = "recording_stop_failed"
    RECORDING_EMPTY = "recording_empty"
    PROCESSING_FAILED = "processing_failed"
    PROCESSING_SKIPPED = "processing_skipped"
    SYNC_FAILED = "sync_failed"
    DAILY_PIPELINE_FAILED = "daily_pipeline_failed"


class ErrorEvent(BaseModel):
    timestamp: datetime
    stage: ErrorStage
    kind: ErrorKind
    task_name: str
    reason: str
    recording_path: str | None = None


def event_for_failure(task_name: str, reason: str) -> ErrorEvent:
    stage, kind = _failure_category(task_name)
    return ErrorEvent(
        timestamp=datetime.now(),
        stage=stage,
        kind=kind,
        task_name=task_name,
        reason=reason,
    )


def event_for_skip(task_name: str, reason: str) -> ErrorEvent:
    return ErrorEvent(
        timestamp=datetime.now(),
        stage=ErrorStage.PROCESSING,
        kind=ErrorKind.PROCESSING_SKIPPED,
        task_name=task_name,
        reason=reason,
    )


def event_for_empty_recording() -> ErrorEvent:
    return ErrorEvent(
        timestamp=datetime.now(),
        stage=ErrorStage.RECORDING,
        kind=ErrorKind.RECORDING_EMPTY,
        task_name="recording_stop",
        reason="recorder returned no usable audio file",
    )


def _failure_category(task_name: str) -> tuple[ErrorStage, ErrorKind]:
    match task_name:
        case "recording_start":
            return ErrorStage.RECORDING, ErrorKind.RECORDING_START_FAILED
        case "recording_stop":
            return ErrorStage.RECORDING, ErrorKind.RECORDING_STOP_FAILED
        case "sync":
            return ErrorStage.SYNC, ErrorKind.SYNC_FAILED
        case "daily_pipeline":
            return ErrorStage.SCHEDULER, ErrorKind.DAILY_PIPELINE_FAILED
        case _:
            return ErrorStage.PROCESSING, ErrorKind.PROCESSING_FAILED
