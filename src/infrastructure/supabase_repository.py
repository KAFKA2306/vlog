import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from src.infrastructure.settings import settings


class SupabaseRepository:
    def __init__(self):
        load_dotenv()
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.client = create_client(url, key) if url and key else None

    def sync(self) -> None:
        if not self.client:
            return

        self._sync_summaries()
        self._sync_novels()

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
            self.client.table("daily_entries").upsert(
                rows, on_conflict="file_path"
            ).execute()

    def _sync_novels(self) -> None:
        rows = []
        novel_dir = Path(settings.novel_out_dir)
        if not novel_dir.exists():
            return

        for path in novel_dir.glob("*.md"):
            # Expecting filename format: YYYYMMDD.md
            if not path.stem.isdigit() or len(path.stem) != 8:
                continue

            date_str = path.stem
            date_obj = datetime.strptime(date_str, "%Y%m%d").date()

            rows.append(
                {
                    "file_path": path.as_posix(),
                    "date": date_obj.isoformat(),
                    "title": f"Novel {date_str}",  # Or use a more descriptive title if available
                    "content": path.read_text(encoding="utf-8"),
                    "tags": ["novel"],
                    "is_public": True,
                }
            )

        if rows:
            self.client.table("novels").upsert(
                rows, on_conflict="file_path"
            ).execute()
