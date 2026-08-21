from datetime import datetime
from pathlib import Path

from vlog_capture.domain.interfaces import ImageGeneratorProtocol, NovelizerProtocol
from vlog_capture.infrastructure.daily_state import DailyStateStore
from vlog_capture.infrastructure.graph_storage import GraphStorage
from vlog_capture.use_cases.daily_artifacts import DailyArtifactManager


class BuildNovelUseCase:
    def __init__(
        self,
        novelizer: NovelizerProtocol,
        image_generator: ImageGeneratorProtocol,
        graph_storage: GraphStorage,
    ):
        self._novelizer = novelizer
        self._image_generator = image_generator
        self._graph_storage = graph_storage
        self._daily_artifacts = DailyArtifactManager(DailyStateStore())

    def execute(self, date: str | None = None) -> Path | None:
        target_date = date or datetime.now().strftime("%Y%m%d")
        return self._daily_artifacts.refresh_novel(
            target_date,
            self._novelizer,
            self._image_generator,
            self._graph_storage,
        )
