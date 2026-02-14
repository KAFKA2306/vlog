import re
from pathlib import Path

from src.infrastructure.ai import ImageGenerator, Novelizer, Summarizer
from src.infrastructure.repositories import FileRepository, SupabaseRepository
from src.infrastructure.system import Transcriber, TranscriptPreprocessor
from src.use_cases.build_novel import BuildNovelUseCase


class PipelineRepairAgent:
    def __init__(self):
        self.data_dir = Path("data")
        self.recordings_dir = self.data_dir / "recordings"
        self.transcripts_dir = self.data_dir / "transcripts"
        self.summaries_dir = self.data_dir / "summaries"
        self.novels_dir = self.data_dir / "novels"
        self.photos_dir = self.data_dir / "photos"

        self.file_repo = FileRepository()

    def run(self):
        print("Pipeline Repair Agent: Starting scan...")

        self._repair_transcripts()
        self._repair_summaries()
        self._repair_novels()
        self._repair_photos()

        print("Pipeline Repair Agent: Scan complete.")
        print("Syncing with Supabase...")
        SupabaseRepository().sync()
        print("Done.")

    def _repair_transcripts(self):
        print("Checking transcripts...")
        if not self.recordings_dir.exists():
            return

        transcriber = None
        preprocessor = None

        for f in self.recordings_dir.glob("*"):
            if f.suffix.lower() not in [".wav", ".flac", ".mp3"]:
                continue

            transcript_path = self.transcripts_dir / f"{f.stem}.txt"
            if not transcript_path.exists():
                print(f"Missing transcript for {f.name}. Repairing...")

                if not transcriber:
                    transcriber = Transcriber()
                    preprocessor = TranscriptPreprocessor()

                transcript, saved_path = transcriber.transcribe_and_save(str(f))
                if transcript and preprocessor:
                    cleaned = preprocessor.process(transcript)
                    cleaned_path = str(
                        Path(saved_path).with_name(f"cleaned_{Path(saved_path).name}")
                    )
                    self.file_repo.save_text(cleaned_path, cleaned)
                print(f"  Repaired: {f.name} -> {Path(saved_path).name}")

        if transcriber:
            transcriber.unload()

    def _repair_summaries(self):
        print("Checking summaries...")
        if not self.transcripts_dir.exists():
            return

        dates = set()
        for f in self.transcripts_dir.glob("*.txt"):
            match = re.search(r"(\d{8})", f.stem)
            if match:
                dates.add(match.group(1))

        summarizer = None

        # Sort dates to process chronologically
        for date_str in sorted(dates):
            summary_path = self.summaries_dir / f"{date_str}_summary.txt"
            if not summary_path.exists():
                print(f"Missing summary for {date_str}. Repairing...")

                # Check for transcripts
                pattern = f"cleaned_{date_str}_*.txt"
                files = sorted(list(self.transcripts_dir.glob(pattern)))
                if not files:
                    pattern = f"{date_str}_*.txt"
                    files = sorted(list(self.transcripts_dir.glob(pattern)))

                if not files:
                    continue

                if not summarizer:
                    summarizer = Summarizer()

                combined_text = ""
                for f in files:
                    text = self.file_repo.read(str(f))
                    combined_text += f"\n\n--- {f.name} ---\n{text}"

                summary = summarizer.summarize(combined_text, date_str=date_str)
                self.file_repo.save_summary(summary, date_str)
                print(f"  Repaired: {date_str}_summary.txt")

    def _repair_novels(self):
        print("Checking novels...")
        if not self.summaries_dir.exists():
            return

        use_case = None

        for f in self.summaries_dir.glob("*_summary.txt"):
            # Filename format: YYYYMMDD_summary.txt
            parts = f.stem.split("_")
            if not parts:
                continue
            date_str = parts[0]

            novel_path = self.novels_dir / f"{date_str}.md"

            if not novel_path.exists():
                print(f"Missing novel for {date_str}. Repairing...")

                if not use_case:
                    use_case = BuildNovelUseCase(Novelizer(), ImageGenerator())

                novel_path = use_case.execute(date_str)
                if novel_path:
                    print(f"  Repaired: {novel_path.name}")

    def _repair_photos(self):
        print("Checking photos...")
        if not self.novels_dir.exists():
            return

        image_generator = None

        for f in self.novels_dir.glob("*.md"):
            # Expect filename format YYYYMMDD.md
            if not (f.stem.isdigit() and len(f.stem) == 8):
                continue

            date_str = f.stem
            photo_path = self.photos_dir / f"{date_str}.png"

            if not photo_path.exists():
                print(f"Missing photo for {date_str}. Repairing...")

                if not image_generator:
                    image_generator = ImageGenerator()

                novel_content = f.read_text(encoding="utf-8")
                self.photos_dir.mkdir(parents=True, exist_ok=True)
                image_generator.generate_from_novel(novel_content, photo_path)
                print(f"  Repaired: {date_str}.png")
