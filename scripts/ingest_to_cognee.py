from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import yaml
from vlog_capture.infrastructure.cognee import cognee_memory
from vlog_capture.portability import runtime_directories


def runtime_paths() -> tuple[Path, Path]:
    directories = runtime_directories()
    return directories.data / "summaries", directories.state / "cognee_queue.yaml"


def load_queue(queue_path: Path) -> dict:
    with queue_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def save_queue(queue_path: Path, queue: dict) -> None:
    queue["last_run"] = datetime.now(timezone.utc).isoformat()
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            queue,
            handle,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )


def get_pending(queue: dict) -> list[dict]:
    batch_size = queue.get("batch_size", 5)
    return [item for item in queue["files"] if item["status"] == "pending"][:batch_size]


async def ingest_file(summary_dir: Path, file_entry: dict) -> None:
    file_path = summary_dir / file_entry["name"]
    content = file_path.read_text(encoding="utf-8")

    name_parts = file_path.stem.split("_")
    metadata = {"source_file": file_path.name}
    if name_parts:
        metadata["date_raw"] = name_parts[0]

    await cognee_memory.add(content, metadata)
    await cognee_memory.cognify()


async def main() -> None:
    summary_dir, queue_path = runtime_paths()
    queue = load_queue(queue_path)
    pending = get_pending(queue)

    if not pending:
        print("No pending files.")
        return

    print(f"Processing {len(pending)} files...")

    for index, entry in enumerate(pending):
        print(f"[{index + 1}/{len(pending)}] {entry['name']}")
        entry["status"] = "processing"
        save_queue(queue_path, queue)

        try:
            await ingest_file(summary_dir, entry)
            entry["status"] = "completed"
            entry["error"] = None
            print("  -> completed")
        except Exception as exc:
            entry["status"] = "failed"
            entry["error"] = str(exc)[:200]
            print(f"  -> failed: {entry['error']}")

        save_queue(queue_path, queue)

    stats: dict[str, int] = {}
    for item in queue["files"]:
        stats[item["status"]] = stats.get(item["status"], 0) + 1
    print(f"\nQueue status: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
