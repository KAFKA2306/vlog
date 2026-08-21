from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import yaml

from vlog_capture.portability import runtime_directories


def runtime_paths() -> tuple[Path, Path]:
    directories = runtime_directories()
    return directories.data / "summaries", directories.state / "cognee_queue.yaml"


def load_queue(queue_path: Path) -> dict:
    if not queue_path.exists():
        return {}
    with queue_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def refresh_queue(summary_dir: Path, queue_path: Path) -> dict:
    existing = load_queue(queue_path)
    existing_by_name = {
        item["name"]: item
        for item in existing.get("files", [])
        if isinstance(item, dict) and "name" in item
    }
    files = [
        existing_by_name.get(
            path.name,
            {"name": path.name, "status": "pending", "error": None},
        )
        for path in sorted(summary_dir.glob("*.txt"))
    ]
    return {
        "batch_size": existing.get("batch_size", 5),
        "last_run": existing.get("last_run"),
        "files": files,
    }


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
    return [
        item for item in queue.get("files", []) if item.get("status") == "pending"
    ][:batch_size]


async def ingest_file(summary_dir: Path, file_entry: dict) -> None:
    from vlog_capture.infrastructure.cognee import cognee_memory

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
    queue = refresh_queue(summary_dir, queue_path)
    save_queue(queue_path, queue)
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
