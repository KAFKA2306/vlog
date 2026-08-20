from __future__ import annotations

from pathlib import Path

import yaml
from vlog_capture.portability import runtime_directories


def runtime_paths() -> tuple[Path, Path]:
    directories = runtime_directories()
    return directories.data / "summaries", directories.state / "cognee_queue.yaml"


def load_existing_queue(queue_path: Path) -> dict:
    if not queue_path.exists():
        return {}
    with queue_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def build_queue(summary_dir: Path | None = None, queue_path: Path | None = None) -> dict:
    default_summary_dir, default_queue_path = runtime_paths()
    summary_dir = summary_dir or default_summary_dir
    queue_path = queue_path or default_queue_path
    existing = load_existing_queue(queue_path)
    existing_map = {item["name"]: item for item in existing.get("files", [])}

    summary_files = sorted(summary_dir.glob("*.txt"))
    files = []
    for summary_file in summary_files:
        if summary_file.name in existing_map:
            files.append(existing_map[summary_file.name])
        else:
            files.append(
                {"name": summary_file.name, "status": "pending", "error": None}
            )

    return {
        "batch_size": existing.get("batch_size", 5),
        "last_run": existing.get("last_run"),
        "files": files,
    }


def main() -> None:
    summary_dir, queue_path = runtime_paths()
    queue = build_queue(summary_dir, queue_path)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            queue,
            handle,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    total = len(queue["files"])
    by_status: dict[str, int] = {}
    for item in queue["files"]:
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1

    print(f"Queue initialized: {total} files")
    print(f"Queue path: {queue_path}")
    for status, count in by_status.items():
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
