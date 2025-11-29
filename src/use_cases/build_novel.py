from datetime import datetime
from pathlib import Path

from src.infrastructure.settings import settings


class BuildNovelUseCase:
    def __init__(self, novelizer):
        self._novelizer = novelizer

    def execute(self, target_date: str | None = None) -> Path | None:
        if not settings.novel_enabled:
            return None

        date_str = target_date or datetime.now().strftime("%Y%m%d")
        summary_path = self._select_summary_file(date_str)
        if not summary_path:
            print(f"Summary file not found for date: {date_str}")
            return None

        today_summary = summary_path.read_text(encoding="utf-8")

        novel_path = self._get_novel_path(date_str)

        chapter = self._novelizer.generate_chapter(today_summary, "")

        novel_path.write_text(chapter, encoding="utf-8")
        return novel_path

    def _select_summary_file(self, date_str: str) -> Path:
        summary_dir = Path(settings.summary_dir)
        candidates = sorted(
            summary_dir.glob(f"{date_str}_*.txt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return None
        return candidates[0]

    def _get_novel_path(self, date_str: str) -> Path:
        out_dir = Path(settings.novel_out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{date_str}.md"
        return out_dir / filename
