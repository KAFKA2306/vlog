import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(self):
        self._log_path = Path("data/traces.jsonl")
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        component: str,
        metadata: dict[str, Any],
        content: str,
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "metadata": metadata,
            "content_chars": len(content),
        }
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
