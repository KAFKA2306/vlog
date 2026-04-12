import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import yaml  # noqa: E402

from src.infrastructure.cognee import cognee_memory  # noqa: E402

QUEUE_PATH = PROJECT_ROOT / "data" / "cognee_queue.yaml"
SUMMARY_DIR = PROJECT_ROOT / "data" / "summaries"


def load_queue() -> dict:
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_queue(queue: dict) -> None:
    queue["last_run"] = datetime.now(timezone.utc).isoformat()
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(
            queue,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )


def get_pending(queue: dict) -> list[dict]:
    batch_size = queue.get("batch_size", 5)
    return [f for f in queue["files"] if f["status"] == "pending"][:batch_size]


async def ingest_file(file_entry: dict) -> None:
    file_path = SUMMARY_DIR / file_entry["name"]
    content = file_path.read_text(encoding="utf-8")

    name_parts = file_path.stem.split("_")
    metadata = {"source_file": file_path.name}
    if len(name_parts) >= 1:
        metadata["date_raw"] = name_parts[0]

    await cognee_memory.add(content, metadata)
    await cognee_memory.cognify()


async def main() -> None:
    queue = load_queue()
    pending = get_pending(queue)

    if not pending:
        print("No pending files.")
        return

    print(f"Processing {len(pending)} files...")

    for i, entry in enumerate(pending):
        print(f"[{i + 1}/{len(pending)}] {entry['name']}")
        entry["status"] = "processing"
        save_queue(queue)

        try:
            await ingest_file(entry)
            entry["status"] = "completed"
            entry["error"] = None
            print("  -> completed")
        except Exception as e:
            entry["status"] = "failed"
            entry["error"] = str(e)[:200]
            print(f"  -> failed: {entry['error']}")

        save_queue(queue)

    stats = {}
    for f in queue["files"]:
        stats[f["status"]] = stats.get(f["status"], 0) + 1
    print(f"\nQueue status: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
