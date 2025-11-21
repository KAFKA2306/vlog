import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


def main() -> None:
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    client = create_client(url, key)
    rows: list[dict[str, object]] = []
    for path in sorted(Path("summaries").glob("*.txt")):
        content = path.read_text(encoding="utf-8")
        stat = path.stat()
        date = datetime.fromtimestamp(stat.st_mtime, timezone.utc).date().isoformat()
        title = path.stem
        rows.append(
            {
                "file_path": str(path),
                "date": date,
                "title": title,
                "content": content,
                "tags": ["summary"],
            }
        )
    if not rows:
        return
    client.table("daily_entries").upsert(rows, on_conflict="file_path").execute()


if __name__ == "__main__":
    main()
