from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from src.infrastructure.image_optimizer import ImageOptimizer
from src.infrastructure.publication import is_publishable_summary
from src.infrastructure.settings import settings
from supabase import create_client

load_dotenv()


@dataclass(frozen=True)
class SyncReport:
    run_id: str
    summaries: int
    novels: int
    photos: int
    evaluations: int

    @property
    def total(self) -> int:
        return self.summaries + self.novels + self.photos + self.evaluations

    def to_dict(self) -> dict[str, int | str | bool]:
        return {
            "run_id": self.run_id,
            "verified": self.total > 0,
            "total": self.total,
            "summaries": self.summaries,
            "novels": self.novels,
            "photos": self.photos,
            "evaluations": self.evaluations,
        }


class StrictSupabaseSync:
    def __init__(self, client: Any | None = None) -> None:
        self.run_id = os.environ.get("VLOG_RUN_ID") or str(uuid4())
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.client: Any = client
        if self.client is None:
            if not url or not key:
                raise RuntimeError(
                    "Supabase is not configured: SUPABASE_URL and "
                    "SUPABASE_SERVICE_ROLE_KEY are required"
                )
            self.client = create_client(url, key)

    def sync(self) -> SyncReport:
        report = SyncReport(
            run_id=self.run_id,
            summaries=self._sync_summaries(),
            novels=self._sync_novels(),
            photos=self._sync_photos(),
            evaluations=self._sync_evaluations(),
        )
        if report.total == 0:
            raise RuntimeError("Supabase sync produced zero verified records")
        self._write_report(report)
        return report

    def _verified_upsert(
        self, table: str, rows: list[dict[str, Any]], on_conflict: str
    ) -> int:
        if not rows:
            return 0
        response = (
            self.client.table(table).upsert(rows, on_conflict=on_conflict).execute()
        )
        data = getattr(response, "data", None)
        if not isinstance(data, list) or len(data) != len(rows):
            actual = len(data) if isinstance(data, list) else "unknown"
            raise RuntimeError(
                f"Supabase verification failed for {table}: "
                f"expected {len(rows)} rows, got {actual}"
            )
        return len(data)

    def _sync_summaries(self) -> int:
        rows: list[dict[str, Any]] = []
        blocked_paths: list[Path] = []
        for path in Path(settings.summary_dir).glob("*_summary.txt"):
            date_str = path.stem.removesuffix("_summary")
            if not is_publishable_summary(date_str):
                blocked_paths.append(path)
                continue
            if not (date_str.isdigit() and len(date_str) == 8):
                continue
            rows.append(
                {
                    "file_path": path.as_posix(),
                    "date": datetime.strptime(date_str, "%Y%m%d").date().isoformat(),
                    "title": path.stem,
                    "content": path.read_text(encoding="utf-8"),
                    "tags": ["summary"],
                    "is_public": True,
                }
            )
        for path in blocked_paths:
            (
                self.client.table("daily_entries")
                .update({"is_public": False})
                .eq("file_path", path.as_posix())
                .execute()
            )
        return self._verified_upsert("daily_entries", rows, "file_path")

    def _sync_novels(self) -> int:
        rows: list[dict[str, Any]] = []
        blocked_paths: list[Path] = []
        for path in Path(settings.novel_out_dir).glob("*.md"):
            if not (path.stem.isdigit() and len(path.stem) == 8):
                continue
            if not is_publishable_summary(path.stem):
                blocked_paths.append(path)
                continue
            rows.append(
                {
                    "file_path": path.as_posix(),
                    "date": datetime.strptime(path.stem, "%Y%m%d").date().isoformat(),
                    "title": f"Novel {path.stem}",
                    "content": path.read_text(encoding="utf-8"),
                    "tags": ["novel"],
                    "is_public": True,
                }
            )
        for path in blocked_paths:
            (
                self.client.table("novels")
                .update({"is_public": False})
                .eq("file_path", path.as_posix())
                .execute()
            )
        return self._verified_upsert("novels", rows, "file_path")

    def _sync_photos(self) -> int:
        verified = 0
        for path in Path(settings.photo_dir).glob("*.png"):
            if not (path.stem.isdigit() and len(path.stem) == 8):
                continue
            date_value = datetime.strptime(path.stem, "%Y%m%d").date().isoformat()
            image_data, extension = ImageOptimizer.to_webp(path)
            storage_path = f"photos/{path.stem}{extension}"
            upload = self.client.storage.from_("vlog-photos").upload(
                storage_path,
                image_data,
                {
                    "content-type": f"image/{extension.lstrip('.')}",
                    "upsert": "true",
                },
            )
            if upload is None:
                raise RuntimeError(f"Storage upload returned no result for {path}")
            image_url = self.client.storage.from_("vlog-photos").get_public_url(
                storage_path
            )
            for table in ("novels", "daily_entries"):
                response = (
                    self.client.table(table)
                    .update({"image_url": image_url})
                    .eq("date", date_value)
                    .execute()
                )
                data = getattr(response, "data", None)
                if not isinstance(data, list) or not data:
                    raise RuntimeError(
                        f"Image URL verification failed for {table} on {date_value}"
                    )
            verified += 1
        return verified

    def _sync_evaluations(self) -> int:
        rows: list[dict[str, Any]] = []
        eval_dir = Path(settings.summary_dir).parent / "evaluations"
        for path in eval_dir.glob("*.json") if eval_dir.exists() else []:
            if not (path.stem.isdigit() and len(path.stem) == 8):
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "date": datetime.strptime(path.stem, "%Y%m%d").date().isoformat(),
                    "target_type": "novel",
                    "score": data.get("quality_score", 0),
                    "reasoning": json.dumps(data, ensure_ascii=False),
                }
            )
        return self._verified_upsert("evaluations", rows, "date,target_type")

    def _write_report(self, report: SyncReport) -> None:
        report_dir = Path("data/sync_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        target = report_dir / f"{self.run_id}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(target)
