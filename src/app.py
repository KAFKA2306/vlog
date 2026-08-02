import logging
import threading
import time
from datetime import datetime

from src.domain.entities import RecordingSession
from src.domain.error_events import event_for_empty_recording
from src.domain.harness import TaskWeight
from src.infrastructure.ai import Summarizer
from src.infrastructure.error_log import ErrorLogRepository
from src.infrastructure.harness import ZeroTrustHarness
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
    def __init__(self):
        self._monitor = ProcessMonitor()
        self._recorder = AudioRecorder()
        self._use_case = ProcessRecordingUseCase(
            transcriber=Transcriber(),
            preprocessor=TranscriptPreprocessor(),
            summarizer=Summarizer(),
            storage=SupabaseRepository(),
            file_repository=FileRepository(),
        )
        self._harness = ZeroTrustHarness()
        self._error_log = ErrorLogRepository()
        self._active_session = None

    def run(self):
        logger.info("Application started")
        while True:
            self._tick()
            time.sleep(settings.check_interval)

    def _tick(self):
        running = self._monitor.is_running()
        if running and not self._active_session:
            logger.info("VRChat process detected. Starting recording session.")
            self._active_session = self._harness.run(
                "recording_start", TaskWeight.LIGHT, self._recorder.start
            )
        if not running and self._active_session:
            logger.info("VRChat process ended. Stopping recording session.")
            file_paths = self._harness.run(
                "recording_stop", TaskWeight.LIGHT, self._recorder.stop
            )
            self._active_session = None
            if file_paths:
                session = RecordingSession(
                    file_paths=file_paths,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                )

                def run_and_sync(session: RecordingSession) -> None:
                    self._use_case.execute_session(session)
                    SupabaseRepository().sync()

                threading.Thread(
                    target=self._harness.run,
                    args=("session_process", TaskWeight.HEAVY, run_and_sync, session),
                    daemon=True,
                ).start()
            else:
                self._error_log.append(event_for_empty_recording())
