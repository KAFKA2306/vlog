import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.infrastructure.settings import settings


class TraceLogger:
    def __init__(self) -> None:
        self._log_path = Path(settings.trace_file)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        component: str,
        model: str,
        start_time: float,
        input_text: str,
        output_text: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": os.environ.get("VLOG_RUN_ID"),
            "task_name": os.environ.get("VLOG_TASK_NAME"),
            "component": component,
            "model": model,
            "latency": round(time.time() - start_time, 4),
            "input_chars": len(input_text),
            "output_chars": len(output_text),
            "metadata": metadata or {},
        }
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
