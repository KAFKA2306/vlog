from datetime import datetime
from pathlib import Path

from src.domain.interfaces import ImageGeneratorProtocol, SummarizerProtocol
from src.infrastructure.settings import settings


class BuildNovelUseCase:
    def __init__(
        self,
        novelizer: SummarizerProtocol,
        image_generator: ImageGeneratorProtocol,
    ):
        self._novelizer = novelizer
        self._image_generator = image_generator

    def execute(self, date: str | None = None) -> Path | None:
        target_date = date or datetime.now().strftime("%Y%m%d")
        summary_path = settings.summary_dir / f"{target_date}_summary.txt"
        if not summary_path.exists():
            return None
        today_summary = summary_path.read_text(encoding="utf-8")
        novel_path = settings.novel_out_dir / f"{target_date}.md"
        novel_so_far = ""
        if novel_path.exists():
            novel_so_far = novel_path.read_text(encoding="utf-8")
        chapter = self._novelizer.generate_novel(today_summary, target_date)
        novel_path.parent.mkdir(parents=True, exist_ok=True)
        if novel_so_far:
            novel_path.write_text(f"{novel_so_far}\n\n{chapter}", encoding="utf-8")
        else:
            novel_path.write_text(chapter, encoding="utf-8")
        photo_path = settings.photo_dir / f"{target_date}.png"
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        self._image_generator.generate_from_novel(chapter, photo_path)
        return novel_path
