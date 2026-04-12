from datetime import datetime
from pathlib import Path

import yaml

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

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
QUEUE_PATH = _PROJECT_ROOT / "data" / "cognee_queue.yaml"


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
        if transcript is None:
            self._finalize(audio_path)
            return False

        summary_text = self._save_summary(transcript, session)
        if summary_text:
            self._update_memory(summary_text, session)

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

        if len(cleaned.encode("utf-8")) <= settings.min_transcript_size_bytes:
            print(f"Transcript too short ({len(cleaned.encode('utf-8'))}B), skipping.")
            for audio_path in session.file_paths:
                self._files.archive(audio_path)
            return

        if transcripts_info:
            _, first_path = transcripts_info[0]
            p = Path(first_path)
            cleaned_path = p.with_name(f"cleaned_{p.name}")
            self._files.save_text(str(cleaned_path), cleaned)

        summary_text = self._save_summary(cleaned, session)
        if summary_text:
            self._update_memory(summary_text, session)

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

    def _save_summary(self, transcript: str, session: RecordingSession) -> str | None:
        target_date = session.start_time.strftime("%Y%m%d")
        summary_path = settings.summary_dir / f"{target_date}_summary.txt"
        summary_path.parent.mkdir(parents=True, exist_ok=True)

        if summary_path.exists():
            print(f"Summary already exists for {target_date}, skipping.")
            return summary_path.read_text(encoding="utf-8")

        pattern = f"cleaned_{target_date}_*.txt"
        daily_files = sorted(settings.transcript_dir.glob(pattern))
        combined_transcript = (
            "\n\n".join(f.read_text(encoding="utf-8") for f in daily_files)
            if daily_files
            else transcript
        )

        summary_text = self._summarizer.summarize(combined_transcript, session)
        self._files.save_text(str(summary_path), summary_text)
        return summary_text

    def _update_memory(self, summary_text: str, session: RecordingSession) -> None:
        target_date = session.start_time.strftime("%Y%m%d")
        summary_name = f"{target_date}_summary.txt"

        if not QUEUE_PATH.exists():
            return

        queue = yaml.safe_load(QUEUE_PATH.read_text(encoding="utf-8"))
        known = {f["name"] for f in queue.get("files", [])}
        if summary_name not in known:
            queue.setdefault("files", []).append(
                {"name": summary_name, "status": "pending", "error": None}
            )
            content = yaml.dump(
                queue,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
            QUEUE_PATH.write_text(content, encoding="utf-8")

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
