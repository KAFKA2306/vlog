import logging

from src.domain.interfaces import (
    DiarizerProtocol,
    FileRepositoryProtocol,
    SummarizerProtocol,
    TranscriberProtocol,
    TranscriptPreprocessorProtocol,
)
from src.models import RecordingSession

logger = logging.getLogger(__name__)


class ProcessRecordingUseCase:
    def __init__(
        self,
        transcriber: TranscriberProtocol,
        preprocessor: TranscriptPreprocessorProtocol,
        summarizer: SummarizerProtocol,
        storage,
        file_repository: FileRepositoryProtocol,
        diarizer: DiarizerProtocol,
    ):
        self.transcriber = transcriber
        self.preprocessor = preprocessor
        self.summarizer = summarizer
        self.storage = storage
        self.file_repository = file_repository
        self.diarizer = diarizer

    def execute_session(self, session: RecordingSession) -> None:
        date_str = session.start_time.strftime("%Y%m%d")
        full_transcript_text = ""

        for path in session.file_paths:
            text, _ = self.transcriber.transcribe_and_save(path)
            full_transcript_text += text + " "

        processed_text = self.preprocessor.process(full_transcript_text)
        novel_content = self.summarizer.generate_novel(processed_text, date_str)

        self.file_repository.save_summary(novel_content, date_str)
        self.storage.sync()
        logger.info(f"Processed recording session for {date_str}")
