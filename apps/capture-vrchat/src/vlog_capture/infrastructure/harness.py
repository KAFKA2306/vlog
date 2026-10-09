import json
import shutil
from datetime import datetime
from typing import Any, Callable

from vlog_capture.domain.error_events import event_for_failure, event_for_skip
from vlog_capture.domain.harness import Incident, IncidentType, TaskWeight
from vlog_capture.infrastructure.error_log import ErrorLogRepository
from vlog_capture.infrastructure.settings import settings
from vlog_capture.infrastructure.system import ProcessMonitor, SystemResourceMonitor


class IncidentLogger:
    def __init__(self) -> None:
        self.path = settings.incident_file

    def log(self, incident: Incident) -> None:
        data = {
            "timestamp": incident.timestamp.isoformat(),
            "task_name": incident.task_name,
            "weight": incident.weight.value,
            "type": incident.type.value,
            "reason": incident.reason,
            "metadata": incident.metadata,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")


class GuardDog:
    def __init__(self) -> None:
        self.monitor = ProcessMonitor()
        self.resources = SystemResourceMonitor()

    def check_safety(self, weight: TaskWeight) -> tuple[bool, str | None]:
        if weight == TaskWeight.LIGHT:
            return True, None

        if self.monitor.is_running():
            return False, "VRChat is running"

        safe, reason, _ = self.resources.is_idle_for_heavy_work()
        if not safe:
            return False, reason

        # Check Disk Space (requires 1GB free)
        usage = shutil.disk_usage(".")
        free_gb = usage.free / (1024**3)
        if free_gb < 1.0:
            return False, f"Low disk space: {free_gb:.2f}GB free"

        return True, None


class ZeroTrustHarness:
    def __init__(self) -> None:
        self.logger = IncidentLogger()
        self.error_log = ErrorLogRepository()
        self.guard = GuardDog()

    def run(
        self,
        task_name: str,
        weight: TaskWeight,
        func: Callable[..., Any],
        *args: Any,
        verify: Callable[[Any], bool] | None = None,
        **kwargs: Any,
    ) -> Any:
        self.logger.log(Incident(datetime.now(), task_name, weight, IncidentType.TRY))

        safe, reason = self.guard.check_safety(weight)
        if not safe:
            self.logger.log(
                Incident(
                    datetime.now(), task_name, weight, IncidentType.SKIPPED, reason
                )
            )
            self.error_log.append(event_for_skip(task_name, reason or "unsafe state"))
            return None

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            self.logger.log(
                Incident(datetime.now(), task_name, weight, IncidentType.FAILED, str(e))
            )
            self.error_log.append(event_for_failure(task_name, str(e)))
            raise

        if verify and not verify(result):
            self.logger.log(
                Incident(
                    datetime.now(), task_name, weight, IncidentType.VERIFICATION_ERROR
                )
            )
            raise RuntimeError(f"Verification failed for task: {task_name}")

        self.logger.log(
            Incident(datetime.now(), task_name, weight, IncidentType.SUCCESS)
        )
        return result
