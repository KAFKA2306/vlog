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
    systemd_notify,
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
_AUDIO_RESOURCE = "audio-input:default"


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
            resource_id="vlog.service",
        )
        systemd_notify("READY=1", "WATCHDOG=1", "STATUS=VLog monitor loop ready")
        try:
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
                        resource_id="vlog.service",
                        retryable=True,
                        error=exc,
                    )
                    # Do not pet the watchdog here. Repeated tick failures force a restart.
                time.sleep(settings.check_interval)
        finally:
            systemd_notify("STOPPING=1", "STATUS=VLog monitor loop stopping")

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
                resource_id="vrchat",
                retryable=True,
                error=exc,
            )
            self._heartbeat("degraded", vrchat_running=None)
            return

        self._events.recover_latest(
            category="monitoring",
            component="process-monitor",
            operation="detect_vrchat",
            resource_id="vrchat",
            message="VRChat process detection recovered",
            code="process_detection_recovered",
        )

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
            resource_id=_AUDIO_RESOURCE,
        )
        try:
            path = self._recorder.start()
            if not path:
                raise RuntimeError("AudioRecorder.start returned no file path")
            self._active_file = path
            self._session_id = session_id
            self._session_started_at = datetime.now()
            self._next_recording_retry_at = 0.0
            logger.info("Recording started: %s", path)
            self._events.emit(
                category="recording",
                component="audio-recorder",
                operation="start",
                status=EventStatus.SUCCEEDED,
                severity=Severity.INFO,
                message="Recording stream opened and thread started",
                code="recording_start",
                session_id=session_id,
                resource_id=_AUDIO_RESOURCE,
                context={"file": path},
            )
            self._events.recover_latest(
                category="recording",
                component="audio-recorder",
                operation="start",
                resource_id=_AUDIO_RESOURCE,
                message="Audio input opened successfully after a prior start failure",
                code="recording_start_recovered",
                session_id=session_id,
                context={"file": path},
            )
            self._events.recover_latest(
                category="recording",
                component="audio-recorder",
                operation="record",
                resource_id=_AUDIO_RESOURCE,
                message="Recording stream remained available and a new session started",
                code="recording_stream_recovered",
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
                resource_id=_AUDIO_RESOURCE,
                retryable=True,
                error=exc,
            )

    def _handle_dead_recorder(self) -> None:
        session_id = self._session_id
        path = self._active_file
        cleanup_error: Exception | None = None
        try:
            self._recorder.stop()
        except Exception as exc:
            cleanup_error = exc
            logger.exception("Recorder cleanup after thread death failed")
        thread_error = self._recorder.last_error
        self._events.emit(
            category="recording",
            component="audio-recorder",
            operation="record",
            status=EventStatus.FAILED,
            severity=Severity.CRITICAL,
            message="Recording thread stopped while VRChat was still running",
            code="recording_thread_died",
            session_id=session_id,
            resource_id=_AUDIO_RESOURCE,
            retryable=True,
            context={
                "file": path,
                "cleanup_error": str(cleanup_error) if cleanup_error else None,
            },
            error=thread_error,
        )
        self._active_file = None
        self._session_id = None
        self._session_started_at = None
        self._next_recording_retry_at = time.monotonic() + 30

    def _stop_recording(self) -> None:
        session_id = self._session_id
        start_time = self._session_started_at or datetime.now()
        active_file = self._active_file
        resource_id = session_id or active_file
        self._events.emit(
            category="recording",
            component="audio-recorder",
            operation="stop",
            status=EventStatus.STARTED,
            severity=Severity.INFO,
            message="VRChat ended; stopping recording",
            code="recording_stop",
            session_id=session_id,
            resource_id=resource_id,
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
                resource_id=resource_id,
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
                resource_id=resource_id,
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
            resource_id=resource_id,
            context={
                "files": list(file_paths),
                "sizes": sizes,
                "duration_seconds": round((end_time - start_time).total_seconds(), 1),
            },
        )
        self._events.recover_latest(
            category="recording",
            component="audio-recorder",
            operation="stop",
            resource_id=resource_id,
            message="Recording stop produced a verified usable audio file",
            code="recording_stop_recovered",
            session_id=session_id,
            context={"files": list(file_paths), "sizes": sizes},
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
        resource_id = session_id or ",".join(session.file_paths)
        self._events.emit(
            category="processing",
            component="recording-pipeline",
            operation="process_session",
            status=EventStatus.STARTED,
            severity=Severity.INFO,
            message="Recorded session processing started",
            code="session_processing",
            session_id=session_id,
            resource_id=resource_id,
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
                resource_id=resource_id,
            )
            self._events.recover_latest(
                category="processing",
                component="recording-pipeline",
                operation="process_session",
                resource_id=resource_id,
                message="Recorded session processing recovered",
                code="session_processing_recovered",
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
                resource_id=resource_id,
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
            resource_id=resource_id,
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
                resource_id=resource_id,
            )
            self._events.recover_latest(
                category="sync",
                component="supabase",
                operation="sync_session",
                resource_id=resource_id,
                message="Session sync recovered",
                code="session_sync_recovered",
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
                resource_id=resource_id,
                retryable=True,
                error=exc,
            )

    def _reap_processing_threads(self) -> None:
        self._processing_threads = {
            thread for thread in self._processing_threads if thread.is_alive()
        }

    def _heartbeat(self, status: str, *, vrchat_running: bool | None) -> None:
        now = time.monotonic()
        if now - self._last_heartbeat_at < 30:
            return
        self._last_heartbeat_at = now
        context = {
            "vrchat_running": vrchat_running,
            "recording": self._recorder.is_recording,
            "active_file": self._active_file,
            "processing_threads": len(self._processing_threads),
        }
        self._events.heartbeat(
            component="vlog-service",
            status=status,
            context=context,
        )
        systemd_notify(
            "WATCHDOG=1",
            f"STATUS=VLog {status}; recording={context['recording']}; workers={context['processing_threads']}",
        )
