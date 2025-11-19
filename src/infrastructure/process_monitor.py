import psutil
from src.infrastructure.settings import settings

class ProcessMonitor:
    def is_running(self) -> bool:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == settings.process_name:
                return True
        return False
