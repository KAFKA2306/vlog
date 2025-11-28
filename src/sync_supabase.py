import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    tz = timezone(timedelta(hours=9))

    existing = {
        r["file_path"]: r["created_at"]
        for r in client.table("daily_entries")
        .select("file_path,created_at")
        .execute()
        .data
    }
    rows = []
    for path in sorted(Path("data/summaries").glob("*.txt")):
        if not path.stem.endswith("_summary"):
            continue
        if "_" in path.stem.replace("_summary", ""):
            continue

        posix = path.as_posix()
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz)
        if (
            posix in existing
            and existing[posix]
            and mtime <= datetime.fromisoformat(existing[posix].replace("Z", "+00:00"))
        ):
            continue

        rows.append(
            {
                "file_path": posix,
                "date": datetime.strptime(path.stem.split("_")[0], "%Y%m%d")
                .date()
                .isoformat(),
                "title": path.stem,
                "content": path.read_text(encoding="utf-8"),
                "tags": ["summary"],
                "is_public": True,
            }
        )

    if not rows:
        return logging.info("No new summaries")
    client.table("daily_entries").upsert(rows, on_conflict="file_path").execute()
    logging.info(f"Synced {len(rows)} entries")

    # Verification
    local, remote = (
        len(list(Path("data/summaries").glob("*.txt"))),
        client.table("daily_entries")
        .select("*", count="exact", head=True)
        .execute()
        .count,
    )
    logging.warning(
        f"Mismatch! {local} vs {remote}"
    ) if local != remote else logging.info(f"Verified: {local}")


if __name__ == "__main__":
    main()
