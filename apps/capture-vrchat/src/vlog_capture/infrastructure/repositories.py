import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from dotenv import load_dotenv
from supabase import Client, create_client
from vlog_capture.infrastructure.image_optimizer import ImageOptimizer
from vlog_capture.infrastructure.publication import is_publishable_summary
from vlog_capture.infrastructure.settings import settings


class FileRepository:
    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def save_text(self, path: str, content: str) -> None:
        Path(path).write_text(content, encoding="utf-8")

    def save_summary(self, summary: str, date_str: str) -> None:
        summary_path = Path(settings.summary_dir) / f"{date_str}_summary.txt"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_text(str(summary_path), summary)

    def archive(self, path: str) -> None:
        if not settings.archive_after_process:
            return
        archive_dir = Path(settings.archive_dir)
        archive_dir.mkdir(exist_ok=True)
        src = Path(path)
        dst = archive_dir / src.name
        src.rename(dst)

    def save_evaluation(self, evaluation: Dict[str, Any], date_str: str) -> None:
        eval_path = (
            Path(settings.summary_dir).parent / "evaluations" / f"{date_str}.json"
        )
        eval_path.parent.mkdir(parents=True, exist_ok=True)
        eval_path.write_text(
            json.dumps(evaluation, indent=2, ensure_ascii=False), encoding="utf-8"
        )


class TaskRepository:
    def __init__(self, file_path: str = "data/tasks.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        return json.loads(self.file_path.read_text(encoding="utf-8"))

    def _save(self, tasks: List[Dict[str, Any]]) -> None:
        self.file_path.write_text(
            json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        tasks = self._load()
        new_task = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            **task_data,
        }
        tasks.append(new_task)
        self._save(tasks)
        return new_task

    def list_pending(self) -> List[Dict[str, Any]]:
        tasks = self._load()
        return [t for t in tasks if t.get("status") != "completed"]

    def complete(self, task_id_prefix: str) -> Dict[str, Any] | None:
        tasks = self._load()
        found = False
        target_task = None
        for task in tasks:
            if task["id"].startswith(task_id_prefix):
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                target_task = task
                found = True
                break
        if found:
            self._save(tasks)
            return target_task
        return None


class SupabaseRepository:
    def __init__(self) -> None:
        load_dotenv()
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.client = create_client(url, key) if url and key else None

    def sync(self) -> None:
        if not self.client:
            return
        client = self.client
        self._sync_summaries(client)
        self._sync_novels(client)
        self._sync_photos(client)
        self._sync_evaluations(client)

    def _sync_summaries(self, client: Client) -> None:
        rows = []
        blocked_paths: list[Path] = []
        summary_dir = Path(settings.summary_dir)
        if not summary_dir.exists():
            return
        for path in summary_dir.glob("*.txt"):
            if not path.stem.endswith("_summary") or "_" in path.stem.replace(
                "_summary", ""
            ):
                continue
            date_str = path.stem.split("_")[0]
            if not is_publishable_summary(date_str):
                blocked_paths.append(path)
                continue
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
        for path in blocked_paths:
            (
                client.table("daily_entries")
                .update({"is_public": False})
                .eq("file_path", path.as_posix())
                .execute()
            )
        if rows:
            client.table("daily_entries").upsert(
                rows, on_conflict="file_path"
            ).execute()

    def _sync_novels(self, client: Client) -> None:
        rows = []
        blocked_paths: list[Path] = []
        novel_dir = Path(settings.novel_out_dir)
        if not novel_dir.exists():
            return
        for path in novel_dir.glob("*.md"):
            if not path.stem.isdigit() or len(path.stem) != 8:
                continue
            date_str = path.stem
            if not is_publishable_summary(date_str):
                blocked_paths.append(path)
                continue
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
        for path in blocked_paths:
            (
                client.table("novels")
                .update({"is_public": False})
                .eq("file_path", path.as_posix())
                .execute()
            )
        if rows:
            client.table("novels").upsert(rows, on_conflict="file_path").execute()

    def _sync_photos(self, client: Client) -> None:
        photo_dir = Path(settings.photo_dir)
        if not photo_dir.exists():
            return
        photo_paths: List[Path] = list(photo_dir.glob("*.png"))
        existing_files: Set[str] = {
            item["name"]
            for item in client.storage.from_("vlog-photos").list(
                "photos", options={"limit": 1000}
            )
        }
        for path in photo_paths:
            if not path.stem.isdigit() or len(path.stem) != 8:
                continue
            date_str: str = path.stem
            file_name: str = f"{date_str}.webp"
            if file_name in existing_files:
                continue
            date_obj: date = datetime.strptime(date_str, "%Y%m%d").date()
            image_data: bytes
            extension: str
            image_data, extension = ImageOptimizer.to_webp(path)
            storage_path: str = f"photos/{file_name}"
            ext_type: str = extension[1:] if extension.startswith(".") else extension
            content_type: str = f"image/{ext_type}"
            if content_type == "image/jpg":
                content_type = "image/jpeg"
            client.storage.from_("vlog-photos").upload(
                storage_path,
                image_data,
                {"content-type": content_type, "upsert": "true"},
            )
            image_url: str = client.storage.from_("vlog-photos").get_public_url(
                storage_path
            )
            client.table("novels").update({"image_url": image_url}).eq(
                "date", date_obj.isoformat()
            ).execute()
            client.table("daily_entries").update({"image_url": image_url}).eq(
                "date", date_obj.isoformat()
            ).execute()

    def _sync_evaluations(self, client: Client) -> None:
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
            client.table("evaluations").upsert(
                rows, on_conflict="date, target_type"
            ).execute()
