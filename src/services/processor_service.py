import logging
from datetime import datetime

from src.domain.entities import DiaryEntry, RecordingSession
from src.infrastructure.diary_writer import DiaryWriter
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.transcriber import Transcriber

logger = logging.getLogger(__name__)


class ProcessorService:
    def __init__(
        self,
        transcriber: Transcriber,
        summarizer: Summarizer,
        diary_writer: DiaryWriter,
    ):
        self._transcriber = transcriber
        self._summarizer = summarizer
        self._diary_writer = diary_writer

    def process_session(self, session: RecordingSession) -> DiaryEntry:
        logger.info(f"Processing session: {session}")
        logger.info("Transcribing audio...")
        transcript = self._transcriber.transcribe(session.file_path)
        self._transcriber.unload()
        logger.info("Summarizing transcript...")
        summary = self._summarizer.summarize(transcript, session)
        completed_at = session.end_time or datetime.now()
        entry = DiaryEntry(
            date=completed_at,
            summary=summary,
            raw_log=transcript,
            session_start=session.start_time,
            session_end=completed_at,
        )
        logger.info("Writing diary entry...")
        diary_path = self._diary_writer.write(entry)
        entry.diary_path = diary_path
        logger.info(f"Processing complete. Diary saved to {diary_path}")
        return entry
