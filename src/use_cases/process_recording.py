from datetime import datetime
from pathlib import Path

from src.domain.entities import RecordingSession
from src.domain.interfaces import (
    DiarizerProtocol,
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
        diarizer: DiarizerProtocol | None = None,
        novelizer: NovelizerProtocol | None = None,
        image_generator: ImageGeneratorProtocol | None = None,
    ):
        self._transcriber = transcriber
        self._diarizer = diarizer
        self._preprocessor = preprocessor
        self._summarizer = summarizer
        self._storage = storage
        self._files = file_repository
        self._novelizer = novelizer
        self._image_generator = image_generator

    def execute(self, audio_path: str) -> bool:
        if not self._files.exists(audio_path):
            return False
        session = self._create_session(audio_path)
        transcript = self._process_transcript(audio_path)
        self._save_summary(transcript, session)
        self._generate_novel_and_photo(session)
        self._finalize(audio_path)
        return True

    def execute_session(self, session: RecordingSession) -> None:
        merged_transcript = ""
        for path in session.file_paths:
            transcript = self._process_with_diarization(path)
            merged_transcript += transcript + "\n"

        self._transcriber.unload()
        # Clean up slightly but keep speaker labels
        # cleaned = self._preprocessor.process(merged_transcript)
        # TODO: Update preprocessor to handle speaker labels or skip for now
        self._save_summary(merged_transcript, session)
        self._storage.sync()
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

    def _process_with_diarization(self, audio_path: str) -> str:
        # Transcribe with timestamps
        segments = self._transcriber.transcribe_segments(audio_path)

        # Diarize if available
        speaker_segments = []
        if self._diarizer:
            speaker_segments = self._diarizer.diarize(audio_path)

        # Merge
        if not speaker_segments:
            text = " ".join(s.text.strip() for s in segments).strip()
            self._save_transcript(audio_path, text)
            return text

        merged_text = ""
        current_speaker = "Unknown"

        # Simple merging strategy: Assign speaker to segment based on overlap
        for segment in segments:
            # Find matching speaker
            best_speaker = current_speaker
            max_overlap = 0

            for start, end, speaker in speaker_segments:
                # Calculate overlap
                seg_start, seg_end = segment.start, segment.end
                overlap_start = max(start, seg_start)
                overlap_end = min(end, seg_end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = speaker

            # Format output
            if best_speaker != current_speaker:
                merged_text += f"\n[{best_speaker}] "
                current_speaker = best_speaker

            merged_text += segment.text.strip() + " "

        final_text = merged_text.strip()
        self._save_transcript(audio_path, final_text)
        return final_text

    def _save_transcript(self, audio_path: str, text: str) -> None:
        base = Path(audio_path).stem
        out_path = settings.transcript_dir / f"{base}.txt"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")

    def _process_transcript(self, audio_path: str) -> str:
        # Backward compatibility for single file execution
        return self._process_with_diarization(audio_path)

    def _save_summary(self, transcript: str, session: RecordingSession) -> None:
        summary_path = (
            settings.summary_dir
            / f"{session.start_time.strftime('%Y%m%d')}_summary.txt"
        )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        if summary_path.exists():
            print(f"Summary already exists for {session.start_time}, skipping.")
            return
        summary_text = self._summarizer.summarize(transcript, session)
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
        if novel_path.exists() and photo_path.exists():
            print(f"Novel and photo already exist for {target_date}, skipping.")
            return
        today_summary = summary_path.read_text(encoding="utf-8")
        if not novel_path.exists():
            novel_so_far = ""
            if novel_path.exists():
                novel_so_far = novel_path.read_text(encoding="utf-8")
            chapter = self._novelizer.generate_chapter(today_summary, novel_so_far)
            novel_path.parent.mkdir(parents=True, exist_ok=True)
            if novel_so_far:
                novel_path.write_text(f"{novel_so_far}\n\n{chapter}", encoding="utf-8")
            else:
                novel_path.write_text(chapter, encoding="utf-8")
        if not photo_path.exists():
            chapter = novel_path.read_text(encoding="utf-8")
            photo_path.parent.mkdir(parents=True, exist_ok=True)
            self._image_generator.generate_from_novel(chapter, photo_path)

    def _finalize(self, audio_path: str) -> None:
        self._storage.sync()
        self._files.archive(audio_path)
