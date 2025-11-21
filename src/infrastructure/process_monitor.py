import logging
import subprocess

import psutil

from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)


class ProcessMonitor:
    def __init__(self):
        self._targets = {name.lower() for name in settings.process_names}
        self._last_status = False

    def is_running(self) -> bool:
        current_status = (
            self._check_linux_processes() or self._check_windows_processes()
        )
        if current_status != self._last_status:
            if current_status:
                logger.info("Target process detected.")
            else:
                logger.info("Target process no longer detected.")
            self._last_status = current_status
        return current_status

    def _check_linux_processes(self) -> bool:
        for proc in psutil.process_iter(["name"]):
            name = proc.info.get("name")
            if name and name.lower() in self._targets:
                return True
        return False

    def _check_windows_processes(self) -> bool:
        result = subprocess.run(["tasklist.exe"], capture_output=True)
        if result.returncode == 0:
            output_lower = result.stdout.decode("utf-8", errors="ignore").lower()
            return any(target in output_lower for target in self._targets)
        return False
