import logging
import threading
import time

from src.infrastructure.audio_recorder import AudioRecorder
from src.infrastructure.file_repository import FileRepository
from src.infrastructure.preprocessor import TranscriptPreprocessor
from src.infrastructure.process_monitor import ProcessMonitor
from src.infrastructure.settings import settings
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.supabase_repository import SupabaseRepository
from src.infrastructure.transcriber import Transcriber
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
        while True:
            self._tick()
            time.sleep(settings.check_interval)

    def _tick(self):
        running = self._monitor.is_running()
        if running and not self._active_session:
            self._active_session = self._recorder.start()
        if not running and self._active_session:
            session = self._recorder.stop()
            self._active_session = None
            if session:
                threading.Thread(
                    target=self._use_case.execute_session, args=(session,), daemon=True
                ).start()
