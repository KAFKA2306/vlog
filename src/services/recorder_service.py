import logging
from datetime import datetime

from src.domain.entities import RecordingSession
from src.infrastructure.audio_recorder import AudioRecorder

logger = logging.getLogger(__name__)


class RecorderService:
    def __init__(self, recorder: AudioRecorder):
        self._recorder = recorder
        self._start_time: datetime | None = None

    @property
    def active_session(self) -> bool:
        return self._start_time is not None

    def start_session(self) -> str:
        if self._start_time:
            return "Already recording"
        file_path = self._recorder.start()
        self._start_time = datetime.now()
        logger.info(f"Started recording to {file_path}")
        return file_path

    def stop_session(self) -> RecordingSession | None:
        if not self._start_time:
            return None
        recorded_paths = self._recorder.stop()
        if not recorded_paths:
            self._start_time = None
            return None
        session = RecordingSession(
            start_time=self._start_time,
            file_paths=recorded_paths,
            end_time=datetime.now(),
        )
        logger.info(f"Stopped recording. Saved {len(recorded_paths)} segment(s)")
        self._start_time = None
        return session
