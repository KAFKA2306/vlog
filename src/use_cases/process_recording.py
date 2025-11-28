from datetime import datetime
from pathlib import Path

from src.domain.entities import RecordingSession
from src.domain.interfaces import (
    FileRepositoryProtocol,
    StorageProtocol,
    SummarizerProtocol,
    TranscriberProtocol,
    TranscriptPreprocessorProtocol,
)


class ProcessRecordingUseCase:
    def __init__(
        self,
        transcriber: TranscriberProtocol,
        preprocessor: TranscriptPreprocessorProtocol,
        summarizer: SummarizerProtocol,
        storage: StorageProtocol,
        file_repository: FileRepositoryProtocol,
    ):
        self._transcriber = transcriber
        self._preprocessor = preprocessor
        self._summarizer = summarizer
        self._storage = storage
        self._files = file_repository

    def execute(self, audio_path: str) -> bool:
        if not self._files.exists(audio_path):
            return False

        transcript, transcript_path = self._transcriber.transcribe_and_save(audio_path)
        self._transcriber.unload()

        basename = Path(audio_path).stem
        start_time = datetime.strptime(basename, "%Y%m%d_%H%M%S")
        session = RecordingSession(
            file_paths=(audio_path,),
            start_time=start_time,
            end_time=datetime.now(),
        )

        cleaned_transcript = self._preprocessor.process(transcript)
        cleaned_path = str(
            Path(transcript_path).with_name(f"cleaned_{Path(transcript_path).name}")
        )
        self._files.save_text(cleaned_path, cleaned_transcript)

        self._summarizer.summarize(cleaned_transcript, session)
        self._storage.sync()
        self._files.archive(audio_path)

        return True

    def execute_session(self, session: RecordingSession) -> None:
        transcripts = [
            self._transcriber.transcribe_and_save(path) for path in session.file_paths
        ]
        self._transcriber.unload()
        merged = " ".join(text for text, _ in transcripts)
        cleaned = self._preprocessor.process(merged)
        self._summarizer.summarize(cleaned, session)
        self._storage.sync()

        for audio_path in session.file_paths:
            self._files.archive(audio_path)
