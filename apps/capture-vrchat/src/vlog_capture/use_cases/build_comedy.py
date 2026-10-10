from datetime import datetime
from pathlib import Path

from vlog_capture.domain.interfaces import ComedyWriterProtocol
from vlog_capture.infrastructure.daily_state import DailyStateStore
from vlog_capture.infrastructure.graph_storage import GraphStorage
from vlog_capture.use_cases.daily_artifacts import DailyArtifactManager


class BuildComedyUseCase:
    def __init__(
        self, comedy_writer: ComedyWriterProtocol, graph_storage: GraphStorage
    ):
        self._comedy_writer = comedy_writer
        self._graph_storage = graph_storage
        self._daily_artifacts = DailyArtifactManager(DailyStateStore())

    def execute(self, date: str | None = None) -> Path | None:
        target_date = date or datetime.now().strftime("%Y%m%d")
        return self._daily_artifacts.refresh_comedy(
            target_date, self._comedy_writer, self._graph_storage
        )
