from __future__ import annotations

import yaml

from vlog_capture.portability import runtime_directories


def main() -> int:
    queue_path = runtime_directories().state / "cognee_queue.yaml"
    if not queue_path.exists():
        print(f"Cognee queue not found: {queue_path}")
        return 1

    queue = yaml.safe_load(queue_path.read_text(encoding="utf-8")) or {}
    files = queue.get("files", [])
    stats: dict[str, int] = {}
    for item in files:
        status = str(item.get("status", "unknown"))
        stats[status] = stats.get(status, 0) + 1

    print(f"Queue: {queue_path}")
    print(f"Total: {len(files)}")
    for status in ("completed", "pending", "processing", "failed", "unknown"):
        if status in stats:
            print(f"  {status}: {stats[status]}")

    failed = [item for item in files if item.get("status") == "failed"]
    if failed:
        print("Failed files:")
        for item in failed:
            print(f"  - {item.get('name')}: {item.get('error')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
