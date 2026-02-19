import logging
import re
from pathlib import Path

from src.infrastructure.ai import ImageGenerator, Summarizer
from src.infrastructure.repositories import FileRepository, SupabaseRepository
from src.infrastructure.system import Transcriber, TranscriptPreprocessor
from src.use_cases.build_novel import BuildNovelUseCase

logger = logging.getLogger(__name__)


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
        self._repair_tasks()
        self._repair_transcripts()
        self._repair_summaries()
        self._repair_novels()
        self._repair_photos()
        self._check_logs()
        SupabaseRepository().sync()

    def _repair_tasks(self):
        from src.infrastructure.repositories import TaskRepository

        repo = TaskRepository()
        tasks = repo._load()
        fixed = False
        for task in tasks:
            status = task.get("status")
            if status in ("discarded", "processing"):
                error = task.get("error", "")
                if error and ("FileNotFoundError" in error or "No such file" in error):
                    if "file_paths" in task:
                        task["file_paths"] = [
                            p.replace("\\", "/") for p in task["file_paths"]
                        ]
                        task["status"] = "pending"
                        task["error"] = None
                        fixed = True
                        logger.info(f"Repaired path for task {task['id']}")
        if fixed:
            repo._save(tasks)

    def _check_logs(self):
        log_path = Path("data/logs/vlog.log")
        if not log_path.exists():
            return
        
        content = log_path.read_text(encoding="utf-8")
        if "AttributeError" in content or "ImportError" in content:
            logger.warning("Critical errors detected in vlog.log. Maintenance required.")

    def _repair_transcripts(self):
        if not self.recordings_dir.exists():
            return
        tr = None
        pr = None
        for f in self.recordings_dir.glob("*"):
            if f.suffix.lower() not in [".wav", ".flac", ".mp3"]:
                continue
            p = self.transcripts_dir / f"{f.stem}.txt"
            if not p.exists():
                if not tr:
                    tr = Transcriber()
                    pr = TranscriptPreprocessor()
                t, sp = tr.transcribe_and_save(str(f))
                if pr:
                    self.file_repo.save_text(
                        str(Path(sp).with_name(f"cleaned_{Path(sp).name}")), pr.process(t)
                    )
        if tr:
            tr.unload()

    def _repair_summaries(self):
        if not self.transcripts_dir.exists():
            return
        dates = {
            match.group(1)
            for f in self.transcripts_dir.glob("*.txt")
            if (match := re.search(r"(\d{8})", f.stem))
        }
        sm = None
        for d in sorted(dates):
            if not (self.summaries_dir / f"{d}_summary.txt").exists():
                fs = sorted(
                    list(self.transcripts_dir.glob(f"cleaned_{d}_*.txt"))
                ) or sorted(list(self.transcripts_dir.glob(f"{d}_*.txt")))
                if not fs:
                    continue
                if not sm:
                    sm = Summarizer()
                self.file_repo.save_summary(
                    sm.generate_novel(
                        "\n\n".join(self.file_repo.read(str(f)) for f in fs), date_str=d
                    ),
                    d,
                )

    def _repair_novels(self):
        if not self.summaries_dir.exists():
            return
        uc = None
        for f in self.summaries_dir.glob("*_summary.txt"):
            d = f.stem.split("_")[0]
            if not (self.novels_dir / f"{d}.md").exists():
                if not uc:
                    uc = BuildNovelUseCase(Summarizer(), ImageGenerator())
                uc.execute(d)

    def _repair_photos(self):
        if not self.novels_dir.exists():
            return
        ig = None
        for f in self.novels_dir.glob("*.md"):
            if not (f.stem.isdigit() and len(f.stem) == 8):
                continue
            d = f.stem
            if not (self.photos_dir / f"{d}.png").exists():
                if not ig:
                    ig = ImageGenerator()
                ig.generate_from_novel(
                    f.read_text(encoding="utf-8"), self.photos_dir / f"{d}.png"
                )
