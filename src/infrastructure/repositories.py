import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from src.infrastructure.settings import settings
from src.models import ActivityTask, DailyEntry, Evaluation
from supabase import create_client

logger = logging.getLogger(__name__)


class FileRepository:
    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def save_text(self, path: str, content: str) -> None:
        Path(path).write_text(content, encoding="utf-8")

    def save_summary(self, content: str, date_str: str) -> None:
        path = Path(settings.summary_dir) / f"{date_str}_summary.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def archive(self, path: str) -> None:
        if not settings.archive_after_process:
            return
        dst = Path(settings.archive_dir) / Path(path).name
        dst.parent.mkdir(exist_ok=True)
        Path(path).rename(dst)

    def save_evaluation(self, evaluation: Evaluation) -> None:
        path = (
            Path(settings.summary_dir).parent
            / "evaluations"
            / f"{evaluation.date.strftime('%Y%m%d')}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            evaluation.model_dump_json(indent=2), encoding="utf-8"
        )


class TaskRepository:
    def __init__(self, path: str = "data/tasks.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[ActivityTask]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [ActivityTask.model_validate(t) for t in data]

    def _save(self, tasks: list[ActivityTask]) -> None:
        self.path.write_text(
            json.dumps(
                [t.model_dump(mode="json") for t in tasks],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def add(self, task: ActivityTask) -> None:
        tasks = self._load()
        tasks.append(task)
        self._save(tasks)

    def list_runnable(self) -> list[ActivityTask]:
        return [t for t in self._load() if t.status in ("pending", "failed")]

    def list_pending(self) -> list[ActivityTask]:
        return [t for t in self._load() if t.status != "completed"]


    def update(self, updated: ActivityTask) -> None:
        tasks = [updated if t.id == updated.id else t for t in self._load()]
        self._save(tasks)

    def complete(self, task: ActivityTask) -> None:
        self.update(task.model_copy(update={"status": "completed", "completed_at": datetime.now()}))


class SupabaseRepository:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.client = create_client(url, key) if url and key else None

    def sync(self) -> None:
        if not self.client:
            return
        self._sync_summaries()
        self._sync_novels()
        self._sync_photos()
        self._sync_evaluations()

    def _sync_summaries(self) -> None:
        summary_dir = Path(settings.summary_dir)
        if not summary_dir.exists():
            return
        paths = [p for p in summary_dir.glob("*.txt") if p.stem.count("_") == 1]
        entries = [
            DailyEntry(
                file_path=p.as_posix(),
                date=datetime.strptime(p.stem.split("_")[0], "%Y%m%d").date(),
                title=p.stem,
                content=p.read_text(encoding="utf-8"),
            )
            for p in paths
        ]
        if entries:
            self.client.table("daily_entries").upsert(
                [e.model_dump(mode="json") for e in entries],
                on_conflict="file_path",
            ).execute()

    def _sync_novels(self) -> None:
        novel_dir = Path(settings.novel_out_dir)
        if not novel_dir.exists():
            return
        paths = [p for p in novel_dir.glob("*.md") if p.stem.isdigit() and len(p.stem) == 8]
        novels = [
            DailyEntry(
                file_path=p.as_posix(),
                date=datetime.strptime(p.stem, "%Y%m%d").date(),
                title=f"Novel {p.stem}",
                content=p.read_text(encoding="utf-8"),
                tags=("novel",),
            )
            for p in paths
        ]
        if novels:
            self.client.table("novels").upsert(
                [n.model_dump(mode="json") for n in novels],
                on_conflict="file_path",
            ).execute()

    def _sync_photos(self) -> None:
        photo_dir = Path(settings.photo_dir)
        if not photo_dir.exists():
            return
        for path in [p for p in photo_dir.glob("*.png") if p.stem.isdigit() and len(p.stem) == 8]:
            date_str = path.stem
            storage_path = f"photos/{date_str}.png"
            self.client.storage.from_("vlog-photos").upload(
                storage_path,
                path.read_bytes(),
                {"content-type": "image/png", "upsert": "true"},
            )
            url = self.client.storage.from_("vlog-photos").get_public_url(storage_path)
            iso_date = datetime.strptime(date_str, "%Y%m%d").date().isoformat()
            self.client.table("novels").update({"image_url": url}).eq("date", iso_date).execute()
            self.client.table("daily_entries").update({"image_url": url}).eq("date", iso_date).execute()

    def _sync_evaluations(self) -> None:
        eval_dir = Path(settings.summary_dir).parent / "evaluations"
        if not eval_dir.exists():
            return
        paths = [p for p in eval_dir.glob("*.json") if p.stem.isdigit() and len(p.stem) == 8]
        evals = []
        for p in paths:
            data = json.loads(p.read_text(encoding="utf-8"))
            evals.append(
                Evaluation(
                    date=datetime.strptime(p.stem, "%Y%m%d").date(),
                    quality_score=data.get("quality_score", 0),
                    faithfulness_score=data.get("faithfulness_score", 0),
                    reasoning=data.get("reasoning", ""),
                )
            )
        if evals:
            rows = [
                {
                    "date": e.date.isoformat(),
                    "target_type": e.target_type,
                    "score": e.quality_score,
                    "reasoning": json.dumps(
                        {
                            "faithfulness": e.faithfulness_score,
                            "quality": e.quality_score,
                            "reasoning": e.reasoning,
                        },
                        ensure_ascii=False,
                    ),
                }
                for e in evals
            ]
            self.client.table("evaluations").upsert(rows, on_conflict="date, target_type").execute()
