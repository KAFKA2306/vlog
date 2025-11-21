import logging
from pathlib import Path

from src.domain.entities import RecordingSession
from src.infrastructure.preprocessor import TranscriptPreprocessor
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.transcriber import Transcriber
from src.sync_supabase import main as sync_supabase

logger = logging.getLogger(__name__)


class ProcessorService:
    def __init__(
        self,
        transcriber: Transcriber,
        summarizer: Summarizer,
        preprocessor: TranscriptPreprocessor,
    ):
        self._transcriber = transcriber
        self._summarizer = summarizer
        self._preprocessor = preprocessor

    def process_session(self, session: RecordingSession) -> str:
        logger.info(f"Processing session: {session}")
        logger.info("Transcribing audio...")
        transcripts = []
        for i, path in enumerate(session.file_paths, 1):
            logger.info(f"Transcribing segment {i}/{len(session.file_paths)}...")
            transcripts.append(self._transcriber.transcribe_and_save(path))
        self._transcriber.unload()

        logger.info("Preprocessing transcript...")
        merged_text = " ".join(text for text, _ in transcripts)
        cleaned_transcript = self._preprocessor.process(merged_text)

        cleaned_path = Path(transcripts[-1][1]).with_name(
            f"cleaned_{Path(transcripts[-1][1]).name}"
        )
        cleaned_path.write_text(cleaned_transcript, encoding="utf-8")
        logger.info(f"Cleaned transcript saved to {cleaned_path}")

        logger.info("Summarizing transcript...")
        summary = self._summarizer.summarize(cleaned_transcript, session)

        date_str = session.start_time.strftime("%Y%m%d")
        summary_path = Path("summaries") / f"{date_str}_summary.txt"
        summary_path.parent.mkdir(exist_ok=True)

        if summary_path.exists():
            existing = summary_path.read_text(encoding="utf-8")
            start = session.start_time.strftime("%H:%M")
            end = (session.end_time or session.start_time).strftime("%H:%M")
            time_range = f"{start}-{end}"
            combined = f"{existing}\n\n---\n\n## Session {time_range}\n\n{summary}"
            summary_path.write_text(combined, encoding="utf-8")
            logger.info(f"Appended to existing daily summary: {summary_path}")
        else:
            summary_path.write_text(summary, encoding="utf-8")
            logger.info(f"Created new daily summary: {summary_path}")

        sync_supabase()

        for path in session.file_paths:
            Path(path).unlink()
            logger.info(f"Deleted processed recording: {path}")

        return str(summary_path)
