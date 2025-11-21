import logging
import threading
import time

from src.infrastructure.audio_recorder import AudioRecorder
from src.infrastructure.diary_writer import DiaryWriter
from src.infrastructure.process_monitor import ProcessMonitor
from src.infrastructure.settings import settings
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.transcriber import Transcriber
from src.services.processor_service import ProcessorService
from src.services.recorder_service import RecorderService

logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self._monitor = ProcessMonitor()
        self._recorder_service = RecorderService(AudioRecorder())
        self._processor_service = ProcessorService(
            Transcriber(),
            Summarizer(),
            DiaryWriter(),
        )
        logger.info("Application initialized")

    def run(self):
        logger.info("Application started")
        while True:
            self._tick()
            time.sleep(settings.check_interval)

    def _tick(self):
        running = self._monitor.is_running()
        active_session = self._recorder_service.active_session
        if running and active_session is None:
            logger.info("VRChat process detected. Starting recording session.")
            self._recorder_service.start_session()
            return
        if not running and active_session is not None:
            logger.info("VRChat process ended. Stopping recording session.")
            session = self._recorder_service.stop_session()
            if session:
                logger.info("Starting background processing for session.")
                threading.Thread(
                    target=self._processor_service.process_session,
                    args=(session,),
                    daemon=True,
                ).start()

    def _shutdown(self):
        logger.info("Shutting down application...")
        session = self._recorder_service.stop_session()
        if session:
            self._processor_service.process_session(session)
