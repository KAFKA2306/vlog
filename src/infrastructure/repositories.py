import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.infrastructure.settings import settings
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
        summary_path = Path(settings.summary_dir) / f"{date_str}_summary.txt"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_text(str(summary_path), content)

    def archive(self, path: str) -> None:
        if not settings.archive_after_process:
            return
        archive_dir = Path(settings.archive_dir)
        archive_dir.mkdir(exist_ok=True)
        src = Path(path)
        dst = archive_dir / src.name
        src.rename(dst)

    def save_evaluation(self, result: Dict[str, Any], date_str: str) -> None:
        eval_path = (
            Path(settings.summary_dir).parent / "evaluations" / f"{date_str}.json"
        )
        eval_path.parent.mkdir(parents=True, exist_ok=True)
        eval_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )


class TaskRepository:
    def __init__(self, file_path: str = "data/tasks.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        content = self.file_path.read_text(encoding="utf-8")
        if not content:
            return []
        return json.loads(content)

    def _save(self, tasks: List[Dict[str, Any]]):
        for task in tasks:
            if "file_paths" in task:
                task["file_paths"] = [p.replace("\\", "/") for p in task["file_paths"]]
        self.file_path.write_text(
            json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        tasks = self._load()
        new_task = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "retry_count": 0,
            **task_data,
        }
        tasks.append(new_task)
        self._save(tasks)
        return new_task

    def list_runnable(self) -> List[Dict[str, Any]]:
        tasks = self._load()
        return [t for t in tasks if t.get("status") in ("pending", "failed")]

    def list_pending(self) -> List[Dict[str, Any]]:
        tasks = self._load()
        return [t for t in tasks if t.get("status") != "completed"]

    def update_status(
        self, task_id: str, status: str, error: str | None = None
    ) -> None:
        tasks = self._load()
        found = False
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now().isoformat()
                if status == "completed":
                    task["completed_at"] = datetime.now().isoformat()
                if error:
                    task["error"] = error
                    task["retry_count"] = task.get("retry_count", 0) + 1
                found = True
                break
        if found:
            self._save(tasks)

    def complete(self, task_id: str) -> None:
        self.update_status(task_id, "completed")


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
        rows = []
        summary_dir = Path(settings.summary_dir)
        if not summary_dir.exists():
            return
        for path in summary_dir.glob("*.txt"):
            if not path.stem.endswith("_summary") or "_" in path.stem.replace(
                "_summary", ""
            ):
                continue
            date_str = path.stem.split("_")[0]
            date_obj = datetime.strptime(date_str, "%Y%m%d").date()
            rows.append(
                {
                    "file_path": path.as_posix(),
                    "date": date_obj.isoformat(),
                    "title": path.stem,
                    "content": path.read_text(encoding="utf-8"),
                    "tags": ["summary"],
                    "is_public": True,
                }
            )
        if rows:
            if not self.client:
                return
            self.client.table("daily_entries").upsert(
                rows, on_conflict="file_path"
            ).execute()

    def _sync_novels(self) -> None:
        rows = []
        novel_dir = Path(settings.novel_out_dir)
        if not novel_dir.exists():
            return
        for path in novel_dir.glob("*.md"):
            if not path.stem.isdigit() or len(path.stem) != 8:
                continue
            date_str = path.stem
            date_obj = datetime.strptime(date_str, "%Y%m%d").date()
            rows.append(
                {
                    "file_path": path.as_posix(),
                    "date": date_obj.isoformat(),
                    "title": f"Novel {date_str}",
                    "content": path.read_text(encoding="utf-8"),
                    "tags": ["novel"],
                    "is_public": True,
                }
            )
        if rows:
            if not self.client:
                return
            self.client.table("novels").upsert(rows, on_conflict="file_path").execute()

    def _sync_photos(self) -> None:
        photo_dir = Path(settings.photo_dir)
        if not photo_dir.exists():
            return
        for path in photo_dir.glob("*.png"):
            if not path.stem.isdigit() or len(path.stem) != 8:
                continue
            date_str = path.stem
            date_obj = datetime.strptime(date_str, "%Y%m%d").date()
            storage_path = f"photos/{date_str}.png"
            if not self.client:
                return
            with open(path, "rb") as f:
                self.client.storage.from_("vlog-photos").upload(
                    storage_path,
                    f.read(),
                    {"content-type": "image/png", "upsert": "true"},
                )
            image_url = self.client.storage.from_("vlog-photos").get_public_url(
                storage_path
            )
            self.client.table("novels").update({"image_url": image_url}).eq(
                "date", date_obj.isoformat()
            ).execute()
            self.client.table("daily_entries").update({"image_url": image_url}).eq(
                "date", date_obj.isoformat()
            ).execute()

    def _sync_evaluations(self) -> None:
        rows = []
        eval_dir = Path(settings.summary_dir).parent / "evaluations"
        if not eval_dir.exists():
            return
        for path in eval_dir.glob("*.json"):
            date_str = path.stem
            if not date_str.isdigit() or len(date_str) != 8:
                continue
            date_obj = datetime.strptime(date_str, "%Y%m%d").date()
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "date": date_obj.isoformat(),
                    "target_type": "novel",
                    "score": data.get("quality_score", 0),
                    "reasoning": json.dumps(
                        {
                            "faithfulness": data.get("faithfulness_score"),
                            "quality": data.get("quality_score"),
                            "reasoning": data.get("reasoning"),
                        },
                        ensure_ascii=False,
                    ),
                }
            )
        if rows:
            if not self.client:
                return
            self.client.table("evaluations").upsert(
                rows, on_conflict="date, target_type"
            ).execute()
