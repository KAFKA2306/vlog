from datetime import datetime
from pathlib import Path

from vlog_capture.domain.entities import RecordingSession
from vlog_capture.domain.interfaces import (
    DailySummarizerProtocol,
    FileRepositoryProtocol,
    ImageGeneratorProtocol,
    NovelizerProtocol,
    StorageProtocol,
    TranscriberProtocol,
    TranscriptPreprocessorProtocol,
)
from vlog_capture.infrastructure.settings import settings
from vlog_capture.use_cases.daily_artifacts import DailyArtifactManager


class ProcessRecordingUseCase:
    def __init__(
        self,
        transcriber: TranscriberProtocol,
        preprocessor: TranscriptPreprocessorProtocol,
        summarizer: DailySummarizerProtocol,
        storage: StorageProtocol,
        file_repository: FileRepositoryProtocol,
        novelizer: NovelizerProtocol | None = None,
        image_generator: ImageGeneratorProtocol | None = None,
        daily_artifacts: DailyArtifactManager | None = None,
    ):
        self._transcriber = transcriber
        self._preprocessor = preprocessor
        self._summarizer = summarizer
        self._storage = storage
        self._files = file_repository
        self._novelizer = novelizer
        self._image_generator = image_generator
        self._daily_artifacts = daily_artifacts or DailyArtifactManager()

    def execute(self, audio_path: str, sync: bool = True) -> bool:
        if not self._files.exists(audio_path):
            return False

        session = self._create_session(audio_path)
        transcript = self._process_transcript(audio_path)
        if transcript is None:
            self._finalize(audio_path)
            return False

        self._save_summary(transcript, session)
        self._generate_novel_and_photo(session)
        self._finalize(audio_path)

        if sync:
            self._storage.sync()

        return True

    def execute_session(self, session: RecordingSession) -> bool:
        transcripts_info = [
            self._transcriber.transcribe_and_save(path) for path in session.file_paths
        ]
        self._transcriber.unload()

        merged = " ".join(text for text, _ in transcripts_info)
        cleaned = self._preprocessor.process(merged)

        if len(cleaned.encode("utf-8")) <= settings.min_transcript_size_bytes:
            print(f"Transcript too short ({len(cleaned.encode('utf-8'))}B), skipping.")
            for audio_path in session.file_paths:
                self._files.archive(audio_path)
            return False

        if transcripts_info:
            _, first_path = transcripts_info[0]
            path = Path(first_path)
            cleaned_path = path.with_name(f"cleaned_{path.name}")
            self._files.save_text(str(cleaned_path), cleaned)

        self._save_summary(cleaned, session)
        self._generate_novel_and_photo(session)

        for audio_path in session.file_paths:
            self._files.archive(audio_path)
        return True

    def _create_session(self, audio_path: str) -> RecordingSession:
        basename = Path(audio_path).stem
        start_time = datetime.strptime(basename, "%Y%m%d_%H%M%S")
        return RecordingSession(
            file_paths=(audio_path,),
            start_time=start_time,
            end_time=datetime.now(),
        )

    def _process_transcript(self, audio_path: str) -> str | None:
        transcript, transcript_path = self._transcriber.transcribe_and_save(audio_path)
        self._transcriber.unload()

        cleaned = self._preprocessor.process(transcript)
        if len(cleaned.encode("utf-8")) <= settings.min_transcript_size_bytes:
            print(f"Transcript too short ({len(cleaned.encode('utf-8'))}B), skipping.")
            return None

        cleaned_path = str(
            Path(transcript_path).with_name(f"cleaned_{Path(transcript_path).name}")
        )
        self._files.save_text(cleaned_path, cleaned)
        return cleaned

    def _save_summary(self, transcript: str, session: RecordingSession) -> None:
        target_date = session.start_time.strftime("%Y%m%d")
        source_paths = self._daily_artifacts.summary_sources_for_date(target_date)
        self._daily_artifacts.refresh_summary(
            target_date,
            self._summarizer,
            self._files,
            source_paths=source_paths if source_paths else None,
            session=session,
            fallback_text=transcript,
        )

    def _generate_novel_and_photo(self, session: RecordingSession) -> None:
        if not (self._novelizer and self._image_generator):
            return

        target_date = session.start_time.strftime("%Y%m%d")
        self._daily_artifacts.refresh_novel(
            target_date,
            self._novelizer,
            self._image_generator,
            None,
        )

    def _finalize(self, audio_path: str) -> None:
        self._files.archive(audio_path)
