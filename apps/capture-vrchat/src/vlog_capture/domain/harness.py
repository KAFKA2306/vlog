from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class TaskWeight(Enum):
    LIGHT = "light"
    HEAVY = "heavy"


class IncidentType(Enum):
    TRY = "try"
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    VERIFICATION_ERROR = "verification_error"


@dataclass
class Incident:
    timestamp: datetime
    task_name: str
    weight: TaskWeight
    type: IncidentType
    reason: str | None = None
    metadata: dict[str, Any] | None = None


class HarnessProtocol(Protocol):
    def run(
        self, task_name: str, weight: TaskWeight, func: Any, *args: Any, **kwargs: Any
    ) -> Any: ...
