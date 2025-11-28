import psutil

from src.infrastructure.settings import settings


class ProcessMonitor:
    def __init__(self):
        self._targets = {name.lower() for name in settings.process_names}
        self._last_status = False

    def is_running(self) -> bool:
        current_status = self._check_processes()
        if current_status != self._last_status:
            self._last_status = current_status
        return current_status

    def _check_processes(self) -> bool:
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info.get("name")
                if name and name.lower() in self._targets:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
