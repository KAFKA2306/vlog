from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_DIR = PROJECT_ROOT / "data" / "summaries"
QUEUE_PATH = PROJECT_ROOT / "data" / "cognee_queue.yaml"


def load_existing_queue() -> dict:
    if not QUEUE_PATH.exists():
        return {}
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_queue() -> dict:
    existing = load_existing_queue()
    existing_map = {f["name"]: f for f in existing.get("files", [])}

    summary_files = sorted(SUMMARY_DIR.glob("*.txt"))
    files = []
    for sf in summary_files:
        if sf.name in existing_map:
            files.append(existing_map[sf.name])
        else:
            files.append({"name": sf.name, "status": "pending", "error": None})

    return {
        "batch_size": existing.get("batch_size", 5),
        "last_run": existing.get("last_run"),
        "files": files,
    }


def main() -> None:
    queue = build_queue()
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(
            queue,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    total = len(queue["files"])
    by_status = {}
    for f in queue["files"]:
        by_status[f["status"]] = by_status.get(f["status"], 0) + 1

    print(f"Queue initialized: {total} files")
    for status, count in by_status.items():
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
