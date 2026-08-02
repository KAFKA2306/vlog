from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from src.domain.entities import RecordingSession
from src.infrastructure.ai import Summarizer
from src.infrastructure.observability import (
    EventStatus,
    OperationalEventLog,
    Severity,
)
from src.infrastructure.repositories import FileRepository, SupabaseRepository
from src.infrastructure.settings import settings
from src.infrastructure.system import (
    AudioRecorder,
    ProcessMonitor,
    Transcriber,
    TranscriptPreprocessor,
)
from src.use_cases.process_recording import ProcessRecordingUseCase

logger = logging.getLogger(__name__)


class Application:
    def __init__(self) -> None:
        self._monitor = ProcessMonitor()
        self._recorder = AudioRecorder()
        self._events = OperationalEventLog()
        self._use_case = ProcessRecordingUseCase(
            transcriber=Transcriber(),
            preprocessor=TranscriptPreprocessor(),
            summarizer=Summarizer(),
            storage=SupabaseRepository(),
            file_repository=FileRepository(),
        )
        self._active_file: str | None = None
        self._session_id: str | None = None
        self._session_started_at: datetime | None = None
        self._processing_threads: set[threading.Thread] = set()
        self._next_recording_retry_at = 0.0
        self._last_heartbeat_at = 0.0

    def run(self) -> None:
        logger.info("Application started")
        self._events.emit(
            category="monitoring",
            component="vlog-service",
            operation="service_loop",
            status=EventStatus.STARTED,
            severity=Severity.INFO,
            message="VLog monitor loop started",
            code="service_started",
        )
        while True:
            try:
                self._tick()
            except Exception as exc:
                logger.exception("Unhandled monitor loop failure")
                self._events.emit(
                    category="monitoring",
                    component="vlog-service",
                    operation="tick",
                    status=EventStatus.FAILED,
                    severity=Severity.CRITICAL,
                    message="Unhandled monitor loop failure",
                    code="monitor_tick_failed",
                    retryable=True,
                    error=exc,
                )
            time.sleep(settings.check_interval)

    def _tick(self) -> None:
        self._reap_processing_threads()
        try:
            running = self._monitor.is_running()
        except Exception as exc:
            logger.exception("VRChat process detection failed")
            self._events.emit(
                category="monitoring",
                component="process-monitor",
                operation="detect_vrchat",
                status=EventStatus.FAILED,
                severity=Severity.ERROR,
                message="VRChat process detection failed",
                code="process_detection_failed",
                retryable=True,
                error=exc,
            )
            self._heartbeat("degraded", vrchat_running=None)
            return

        if running and self._active_file and not self._recorder.is_recording:
            self._handle_dead_recorder()

        if running and not self._active_file:
            if time.monotonic() >= self._next_recording_retry_at:
                self._start_recording()
        elif not running and self._active_file:
            self._stop_recording()

        self._heartbeat("healthy", vrchat_running=running)

    def _start_recording(self) -> None:
        session_id = str(uuid4())
        self._events.emit(
            category="recording",
            component="audio-recorder",
            operation="start",
            status=EventStatus.STARTED,
            severity=Severity.INFO,
            message="VRChat detected; starting recording",
            code="recording_start",
            session_id=session_id,
        )
        try:
            path = self._recorder.start()
            if not path:
                raise RuntimeError("AudioRecorder.start returned no file path")
            self._active_file = path
            self._session_id = session_id
            self._session_started_at = datetime.now()
            logger.info("Recording started: %s", path)
            self._events.emit(
                category="recording",
                component="audio-recorder",
                operation="start",
                status=EventStatus.SUCCEEDED,
                severity=Severity.INFO,
                message="Recording thread started",
                code="recording_start",
                session_id=session_id,
                context={"file": path},
            )
        except Exception as exc:
            self._next_recording_retry_at = time.monotonic() + 30
            logger.exception("Recording start failed")
            self._events.emit(
                category="recording",
                component="audio-recorder",
                operation="start",
                status=EventStatus.FAILED,
                severity=Severity.CRITICAL,
                message="Recording start failed; retry scheduled in 30 seconds",
                code="recording_start_failed",
                session_id=session_id,
                retryable=True,
                error=exc,
            )

    def _handle_dead_recorder(self) -> None:
        session_id = self._session_id
        path = self._active_file
        try:
            self._recorder.stop()
        except Exception:
            logger.exception("Recorder cleanup after thread death failed")
        self._events.emit(
            category="recording",
            component="audio-recorder",
            operation="record",
            status=EventStatus.FAILED,
            severity=Severity.CRITICAL,
            message="Recording thread stopped while VRChat was still running",
            code="recording_thread_died",
            session_id=session_id,
            retryable=True,
            context={"file": path},
        )
        self._active_file = None
        self._session_id = None
        self._session_started_at = None
        self._next_recording_retry_at = time.monotonic() + 30

    def _stop_recording(self) -> None:
        session_id = self._session_id
        start_time = self._session_started_at or datetime.now()
        active_file = self._active_file
        self._events.emit(
            category="recording",
            component="audio-recorder",
            operation="stop",
            status=EventStatus.STARTED,
            severity=Severity.INFO,
            message="VRChat ended; stopping recording",
            code="recording_stop",
            session_id=session_id,
            context={"file": active_file},
        )
        try:
            file_paths = self._recorder.stop()
        except Exception as exc:
            logger.exception("Recording stop failed")
            self._events.emit(
                category="recording",
                component="audio-recorder",
                operation="stop",
                status=EventStatus.FAILED,
                severity=Severity.CRITICAL,
                message="Recording stop failed",
                code="recording_stop_failed",
                session_id=session_id,
                retryable=False,
                error=exc,
                context={"file": active_file},
            )
            file_paths = None
        finally:
            self._active_file = None
            self._session_id = None
            self._session_started_at = None

        if not file_paths:
            self._events.emit(
                category="recording",
                component="audio-recorder",
                operation="stop",
                status=EventStatus.FAILED,
                severity=Severity.WARNING,
                message="Recording ended without a usable audio file",
                code="empty_recording",
                session_id=session_id,
                retryable=False,
                context={"file": active_file},
            )
            return

        sizes = {
            path: Path(path).stat().st_size if Path(path).exists() else 0
            for path in file_paths
        }
        end_time = datetime.now()
        self._events.emit(
            category="recording",
            component="audio-recorder",
            operation="stop",
            status=EventStatus.SUCCEEDED,
            severity=Severity.INFO,
            message="Recording stopped with usable audio",
            code="recording_stop",
            session_id=session_id,
            context={
                "files": list(file_paths),
                "sizes": sizes,
                "duration_seconds": round((end_time - start_time).total_seconds(), 1),
            },
        )
        session = RecordingSession(
            file_paths=file_paths,
            start_time=start_time,
            end_time=end_time,
        )
        worker = threading.Thread(
            target=self._process_and_sync,
            args=(session, session_id),
            name=f"vlog-process-{session_id}",
            daemon=False,
        )
        self._processing_threads.add(worker)
        worker.start()

    def _process_and_sync(
        self, session: RecordingSession, session_id: str | None
    ) -> None:
        self._events.emit(
            category="processing",
            component="recording-pipeline",
            operation="process_session",
            status=EventStatus.STARTED,
            severity=Severity.INFO,
            message="Recorded session processing started",
            code="session_processing",
            session_id=session_id,
            context={"files": list(session.file_paths)},
        )
        try:
            self._use_case.execute_session(session)
            self._events.emit(
                category="processing",
                component="recording-pipeline",
                operation="process_session",
                status=EventStatus.SUCCEEDED,
                severity=Severity.INFO,
                message="Recorded session processing completed",
                code="session_processing",
                session_id=session_id,
            )
        except Exception as exc:
            logger.exception("Recorded session processing failed")
            self._events.emit(
                category="processing",
                component="recording-pipeline",
                operation="process_session",
                status=EventStatus.FAILED,
                severity=Severity.CRITICAL,
                message="Recorded session processing failed",
                code="session_processing_failed",
                session_id=session_id,
                retryable=True,
                error=exc,
                context={"files": list(session.file_paths)},
            )
            return

        self._events.emit(
            category="sync",
            component="supabase",
            operation="sync_session",
            status=EventStatus.STARTED,
            severity=Severity.INFO,
            message="Session sync started",
            code="session_sync",
            session_id=session_id,
        )
        try:
            SupabaseRepository().sync()
            self._events.emit(
                category="sync",
                component="supabase",
                operation="sync_session",
                status=EventStatus.SUCCEEDED,
                severity=Severity.INFO,
                message="Session sync completed",
                code="session_sync",
                session_id=session_id,
            )
        except Exception as exc:
            logger.exception("Session sync failed")
            self._events.emit(
                category="sync",
                component="supabase",
                operation="sync_session",
                status=EventStatus.FAILED,
                severity=Severity.ERROR,
                message="Session sync failed",
                code="session_sync_failed",
                session_id=session_id,
                retryable=True,
                error=exc,
            )

    def _reap_processing_threads(self) -> None:
        self._processing_threads = {
            thread for thread in self._processing_threads if thread.is_alive()
        }

    def _heartbeat(self, status: str, *, vrchat_running: bool | None) -> None:
        now = time.monotonic()
        if now - self._last_heartbeat_at < 60:
            return
        self._last_heartbeat_at = now
        self._events.heartbeat(
            component="vlog-service",
            status=status,
            context={
                "vrchat_running": vrchat_running,
                "recording": self._recorder.is_recording,
                "active_file": self._active_file,
                "processing_threads": len(self._processing_threads),
            },
        )
