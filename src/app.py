import time
import sys
import subprocess
from src.infrastructure.settings import settings
from src.infrastructure.process_monitor import ProcessMonitor
from src.infrastructure.transcriber import Transcriber
from src.infrastructure.summarizer import Summarizer
import os
from datetime import datetime

class Application:
    def __init__(self):
        self.monitor = ProcessMonitor()
        self.recorder_process = None

    def run(self):
        while True:
            is_running = self.monitor.is_running()

            if is_running and self.recorder_process is None:
                self.recorder_process = subprocess.Popen(
                    [sys.executable, "-m", "src.services.recorder_service"]
                )
            
            elif not is_running and self.recorder_process is not None:
                self.recorder_process.terminate()
                self.recorder_process.wait()
                self.recorder_process = None
                self.process_recording()
                
            time.sleep(settings.check_interval)

    def process_recording(self):
        # This logic should ideally be in a separate service or triggered async
        # For simplicity in this refactor, we'll keep the synchronous trigger logic
        # but move the actual processing to a separate script execution to avoid blocking
        subprocess.Popen([sys.executable, "-m", "src.services.processor_service"])

