import logging
import threading
import time
from datetime import datetime
from src.domain.entities import RecordingSession
from src.infrastructure.ai import Summarizer
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
            self._active_session = self._recorder.start()
        if not running and self._active_session:
            logger.info("VRChat process ended. Stopping recording session.")
            file_paths = self._recorder.stop()
            self._active_session = None
            if file_paths:
                session = RecordingSession(
                    file_paths=file_paths,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                )
                threading.Thread(
                    target=self._use_case.execute_session, args=(session,), daemon=True
                ).start()
