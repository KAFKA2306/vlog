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
        texts: list[str] = []
        transcript_paths: list[str] = []
        for path in session.file_paths:
            text, transcript_path = self._transcriber.transcribe_and_save(path)
            texts.append(text)
            transcript_paths.append(transcript_path)
        self._transcriber.unload()

        logger.info("Preprocessing transcript...")
        merged = " ".join(texts)
        cleaned_transcript = self._preprocessor.process(merged)

        last_transcript = Path(transcript_paths[-1])
        cleaned_path = last_transcript.with_name(
            f"cleaned_{last_transcript.name}"
        )
        cleaned_path.write_text(cleaned_transcript, encoding="utf-8")
        logger.info(f"Cleaned transcript saved to {cleaned_path}")

        logger.info("Summarizing transcript...")
        summary = self._summarizer.summarize(cleaned_transcript, session)

        summary_name = f"{Path(session.file_paths[0]).stem}_summary.txt"
        summary_path = Path("summaries") / summary_name
        summary_path.parent.mkdir(exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")

        logger.info("Processing complete. Summary saved to %s", summary_path)
        sync_supabase()
        return str(summary_path)
