import logging
import time
from datetime import datetime
from pathlib import Path

from src.infrastructure.agents.pipeline_repair import PipelineRepairAgent
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
from src.models import ActivityTask, RecordingSession
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

        repair_agent = PipelineRepairAgent()
        while True:
            repair_agent.run()
            self._tick()
            self._work()
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

        for task_data in runnable:
            task = ActivityTask(**task_data)
            task_id = task.id
            if not task.type:
                logger.error(
                    f"Task {task_id} missing 'type' field. Marking as discarded."
                )
                tasks.update_status(task_id, "discarded", error="Missing 'type' field")
                continue

            logger.info(f"Processing task {task_id} ({task.type})")
            tasks.update_status(task_id, "processing")

            if task.type == "process_session":
                paths = [p.replace("\\", "/") for p in task.file_paths]
                paths = [Path(p).as_posix() for p in paths]
                start_time_iso = task.start_time or datetime.now().isoformat()
                session = RecordingSession(
                    file_paths=tuple(paths),
                    start_time=datetime.fromisoformat(start_time_iso),
                    end_time=datetime.now(),
                )
                self._use_case.execute_session(session)

            elif task.type == "generate_photo":
                novel_path = Path(task.novel_path) if task.novel_path else None
                if novel_path and novel_path.exists() and task.photo_path:
                    chapter = novel_path.read_text(encoding="utf-8")
                    output_path = Path(task.photo_path)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    self._image_generator.generate_from_novel(chapter, output_path)
                else:
                    logger.warning(f"Novel not found for task {task_id}: {novel_path}")

            tasks.complete(task_id)
            logger.info(f"Task {task_id} completed successfully")
