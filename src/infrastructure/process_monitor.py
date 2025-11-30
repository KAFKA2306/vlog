import logging

import psutil

from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)


class ProcessMonitor:
    def __init__(self):
        self._targets = {name.lower() for name in settings.process_names}
        self._last_status = False
        self._logged_sample = False

    def is_running(self) -> bool:
        current_status = self._check_processes()
        if current_status != self._last_status:
            self._last_status = current_status
            if current_status:
                logger.info("Target process detected.")
                self._logged_sample = False
            else:
                logger.info("Target process no longer detected.")
        if not current_status and not self._logged_sample:
            sample = self._sample_processes()
            logger.info("No target found. Sample running processes: %s", sample)
            self._logged_sample = True
        return current_status

    def _check_processes(self) -> bool:
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                name = (proc.info.get("name") or "").lower()
                exe = (proc.info.get("exe") or "").lower()
                if name in self._targets or exe in self._targets:
                    return True
                if any(target in name for target in self._targets):
                    return True
                if any(target in exe for target in self._targets):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False

    def _sample_processes(self) -> list[str]:
        names = []
        for proc in psutil.process_iter(["name"]):
            if len(names) >= 10:
                break
            try:
                name = proc.info.get("name")
                if name:
                    names.append(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return names
