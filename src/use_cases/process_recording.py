from datetime import datetime
from pathlib import Path

from src.domain.entities import RecordingSession
from src.domain.interfaces import (
    FileRepositoryProtocol,
    ImageGeneratorProtocol,
    NovelizerProtocol,
    StorageProtocol,
    SummarizerProtocol,
    TranscriberProtocol,
    TranscriptPreprocessorProtocol,
)
from src.infrastructure.settings import settings


class ProcessRecordingUseCase:
    def __init__(
        self,
        transcriber: TranscriberProtocol,
        preprocessor: TranscriptPreprocessorProtocol,
        summarizer: SummarizerProtocol,
        storage: StorageProtocol,
        file_repository: FileRepositoryProtocol,
        novelizer: NovelizerProtocol | None = None,
        image_generator: ImageGeneratorProtocol | None = None,
    ):
        self._transcriber = transcriber
        self._preprocessor = preprocessor
        self._summarizer = summarizer
        self._storage = storage
        self._files = file_repository
        self._novelizer = novelizer
        self._image_generator = image_generator

    def execute(self, audio_path: str, sync: bool = True) -> bool:
        if not self._files.exists(audio_path):
            return False

        session = self._create_session(audio_path)
        transcript = self._process_transcript(audio_path)
        self._save_summary(transcript, session)
        self._generate_novel_and_photo(session)
        self._finalize(audio_path)

        if sync:
            self._storage.sync()

        return True

    def execute_session(self, session: RecordingSession) -> None:
        transcripts_info = [
            self._transcriber.transcribe_and_save(path) for path in session.file_paths
        ]
        self._transcriber.unload()

        merged = " ".join(text for text, _ in transcripts_info)
        cleaned = self._preprocessor.process(merged)

        if transcripts_info:
            _, first_path = transcripts_info[0]
            p = Path(first_path)
            cleaned_path = p.with_name(f"cleaned_{p.name}")
            self._files.save_text(str(cleaned_path), cleaned)

        self._save_summary(cleaned, session)
        self._generate_novel_and_photo(session)

        for audio_path in session.file_paths:
            self._files.archive(audio_path)

    def _create_session(self, audio_path: str) -> RecordingSession:
        basename = Path(audio_path).stem
        start_time = datetime.strptime(basename, "%Y%m%d_%H%M%S")
        return RecordingSession(
            file_paths=(audio_path,),
            start_time=start_time,
            end_time=datetime.now(),
        )

    def _process_transcript(self, audio_path: str) -> str:
        transcript, transcript_path = self._transcriber.transcribe_and_save(audio_path)
        self._transcriber.unload()

        cleaned = self._preprocessor.process(transcript)
        cleaned_path = str(
            Path(transcript_path).with_name(f"cleaned_{Path(transcript_path).name}")
        )
        self._files.save_text(cleaned_path, cleaned)
        return cleaned

    def _save_summary(self, transcript: str, session: RecordingSession) -> None:
        target_date = session.start_time.strftime("%Y%m%d")
        summary_path = settings.summary_dir / f"{target_date}_summary.txt"
        summary_path.parent.mkdir(parents=True, exist_ok=True)

        if summary_path.exists():
            print(f"Summary already exists for {target_date}, skipping.")
            return

        pattern = f"cleaned_{target_date}_*.txt"
        daily_files = sorted(settings.transcript_dir.glob(pattern))
        combined_transcript = (
            "\n\n".join(f.read_text(encoding="utf-8") for f in daily_files)
            if daily_files
            else transcript
        )

        summary_text = self._summarizer.summarize(combined_transcript, session)
        self._files.save_text(str(summary_path), summary_text)

    def _generate_novel_and_photo(self, session: RecordingSession) -> None:
        if not (self._novelizer and self._image_generator):
            return

        target_date = session.start_time.strftime("%Y%m%d")
        summary_path = settings.summary_dir / f"{target_date}_summary.txt"

        if not summary_path.exists():
            return

        novel_path = settings.novel_out_dir / f"{target_date}.md"
        photo_path = settings.photo_dir / f"{target_date}.png"

        novel_files = sorted(list(settings.novel_out_dir.glob("*.md")))
        prev_files = [f for f in novel_files if f.name < f"{target_date}.md"]
        novel_so_far = prev_files[-1].read_text(encoding="utf-8") if prev_files else ""

        today_summary = summary_path.read_text(encoding="utf-8")
        chapter = self._novelizer.generate_chapter(today_summary, novel_so_far)

        novel_path.parent.mkdir(parents=True, exist_ok=True)
        novel_path.write_text(chapter, encoding="utf-8")

        photo_path.parent.mkdir(parents=True, exist_ok=True)
        self._image_generator.generate_from_novel(chapter, photo_path)

    def _finalize(self, audio_path: str) -> None:
        self._files.archive(audio_path)
