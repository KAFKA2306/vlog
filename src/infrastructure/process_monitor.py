import subprocess

import psutil

from src.infrastructure.settings import settings


class ProcessMonitor:
    def __init__(self):
        self._targets = {name.lower() for name in settings.process_names}

    def is_running(self) -> bool:
        if self._check_linux_processes():
            return True
        return self._check_windows_processes()

    def _check_linux_processes(self) -> bool:
        for proc in psutil.process_iter(["name"]):
            name = proc.info.get("name")
            if name and name.lower() in self._targets:
                return True
        return False

    def _check_windows_processes(self) -> bool:
        try:
            result = subprocess.run(
                ["tasklist.exe"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                output_lower = result.stdout.decode("utf-8", errors="ignore").lower()
                return any(target in output_lower for target in self._targets)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False
