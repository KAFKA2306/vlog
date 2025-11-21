import logging
from datetime import datetime

from src.domain.entities import RecordingSession
from src.infrastructure.audio_recorder import AudioRecorder

logger = logging.getLogger(__name__)


class RecorderService:
    def __init__(self, recorder: AudioRecorder):
        self._recorder = recorder
        self._active_session: RecordingSession | None = None

    @property
    def active_session(self) -> RecordingSession | None:
        return self._active_session

    def start_session(self) -> RecordingSession:
        if self._active_session:
            return self._active_session
        file_path = self._recorder.start()
        logger.info(f"Started recording to {file_path}")
        session = RecordingSession(
            start_time=datetime.now(), file_paths=(file_path,)
        )
        self._active_session = session
        return session

    def stop_session(self) -> RecordingSession | None:
        if not self._active_session:
            return None
        recorded_paths = (
            self._recorder.stop() or self._active_session.file_paths
        )
        session = RecordingSession(
            start_time=self._active_session.start_time,
            file_paths=recorded_paths,
            end_time=datetime.now(),
        )
        logger.info(f"Stopped recording. Saved to {recorded_paths[-1]}")
        self._active_session = None
        return session
