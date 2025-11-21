import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from supabase import create_client

logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(url, key)

    tz = ZoneInfo("Asia/Tokyo")
    existing = {
        r["file_path"]: r["updated_at"]
        for r in client.table("daily_entries")
        .select("file_path,updated_at")
        .execute()
        .data
    }

    rows: list[dict[str, object]] = []
    for path in sorted(Path("summaries").glob("*.txt")):
        posix_path = path.as_posix()
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz)

        if posix_path in existing and existing[posix_path]:
            last_sync = datetime.fromisoformat(
                existing[posix_path].replace("Z", "+00:00")
            )
            if mtime <= last_sync:
                continue

        content = path.read_text(encoding="utf-8")
        date_str = path.stem.split("_")[0]
        date = datetime.strptime(date_str, "%Y%m%d").date().isoformat()

        rows.append(
            {
                "file_path": posix_path,
                "date": date,
                "title": path.stem,
                "content": content,
                "tags": ["summary"],
            }
        )

    if not rows:
        logger.info("No new summaries to sync")
        return

    client.table("daily_entries").upsert(rows, on_conflict="file_path").execute()
    logger.info(f"Synced {len(rows)} entries to Supabase")


if __name__ == "__main__":
    main()
