from datetime import datetime
from typing import Any, Dict

from src.infrastructure.ai import Curator
from src.infrastructure.repositories import FileRepository, SupabaseRepository
from src.infrastructure.settings import settings


class EvaluateDailyContentUseCase:
    def __init__(
        self,
        curator: Curator | None = None,
        file_repository: FileRepository | None = None,
        storage: SupabaseRepository | None = None,
    ):
        self._curator = curator or Curator()
        self._files = file_repository or FileRepository()
        self._storage = storage or SupabaseRepository()

    def execute(self, date_str: str | None = None) -> Dict[str, Any] | None:
        target_date = date_str or datetime.now().strftime("%Y%m%d")
        summary_path = settings.summary_dir / f"{target_date}_summary.txt"
        novel_path = settings.novel_out_dir / f"{target_date}.md"
        if not summary_path.exists() or not novel_path.exists():
            return None
        summary_text = self._files.read(str(summary_path))
        novel_text = self._files.read(str(novel_path))
        result = self._curator.evaluate(summary_text, novel_text)
        self._files.save_evaluation(result, target_date)
        self._storage.sync()
        return result
