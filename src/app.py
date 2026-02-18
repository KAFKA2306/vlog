import logging
import time
from datetime import datetime
from pathlib import Path

from src.domain.entities import RecordingSession
from src.infrastructure.ai import ImageGenerator, Summarizer
from src.infrastructure.repositories import (
    FileRepository,
    SupabaseRepository,
    TaskRepository,
)
from src.infrastructure.settings import settings
from src.infrastructure.system import (
    AudioRecorder,
    Diarizer,
    ProcessMonitor,
    Transcriber,
    TranscriptPreprocessor,
)
from src.use_cases.process_recording import ProcessRecordingUseCase

logger = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self._monitor = ProcessMonitor()
        self._recorder = AudioRecorder()
        self._use_case = ProcessRecordingUseCase(
            transcriber=Transcriber(),
            preprocessor=TranscriptPreprocessor(),
            summarizer=Summarizer(),
            storage=SupabaseRepository(),
            file_repository=FileRepository(),
            diarizer=Diarizer(),
        )
        self._image_generator = ImageGenerator()
        self._active_session = None

    def run(self):
        logger.info("Application started with Task-Driven Architecture")
        while True:
            try:
                self._tick()
                self._work()
            except Exception as e:
                logger.error(f"Critical error in main loop: {e}")
                raise  # Crash-on-fail
            time.sleep(settings.check_interval)

    def _tick(self):
        running = self._monitor.is_running()
        if running and not self._active_session:
            logger.info("VRChat process detected. Starting recording session.")
            self._active_session = self._recorder.start()
        elif not running and self._active_session:
            logger.info("VRChat process ended. Stopping recording.")
            file_paths = self._recorder.stop()
            self._active_session = None
            if file_paths:
                tasks = TaskRepository()
                tasks.add(
                    {
                        "type": "process_session",
                        "file_paths": list(file_paths),
                        "start_time": datetime.now().isoformat(),
                    }
                )

    def _work(self):
        tasks = TaskRepository()
        runnable = tasks.list_runnable()
        if not runnable:
            return

        for task in runnable:
            task_id = task["id"]
            if "type" not in task:
                logger.error(f"Task {task_id} missing 'type' field. Marking as failed.")
                tasks.update_status(task_id, "failed", error="Missing 'type' field")
                continue

            logger.info(f"Processing task {task_id} ({task['type']})")
            tasks.update_status(task_id, "processing")

            try:
                if task["type"] == "process_session":
                    session = RecordingSession(
                        file_paths=tuple(task["file_paths"]),
                        start_time=datetime.fromisoformat(task["start_time"]),
                        end_time=datetime.now(),
                    )
                    self._use_case.execute_session(session)

                elif task["type"] == "generate_photo":
                    novel_path = Path(task["novel_path"])
                    if novel_path.exists():
                        chapter = novel_path.read_text(encoding="utf-8")
                        output_path = Path(task["photo_path"])
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        self._image_generator.generate_from_novel(chapter, output_path)
                    else:
                        logger.warning(
                            f"Novel not found for task {task_id}: {novel_path}"
                        )

                tasks.complete(task_id)
                logger.info(f"Task {task_id} completed successfully")
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                tasks.update_status(task_id, "failed", error=str(e))
                raise  # Crash-on-fail to ensure clean state on restart
