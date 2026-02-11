import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
class TraceLogger:
    def __init__(self):
        self._log_path = Path("data/traces.jsonl")
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
    def log(
        self,
        component: str,
        model: str,
        start_time: float,
        input_text: str,
        output_text: str,
        metadata: Dict[str, Any] = None,
    ) -> None:
        latency = time.time() - start_time
        entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "model": model,
            "latency": round(latency, 4),
            "input_chars": len(input_text),
            "output_chars": len(output_text),
            "metadata": metadata or {},
        }
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
