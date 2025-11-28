from pathlib import Path

from src.infrastructure.settings import settings


class FileRepository:
    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def save_text(self, path: str, content: str) -> None:
        Path(path).write_text(content, encoding="utf-8")

    def archive(self, path: str) -> None:
        if not settings.archive_after_process:
            return

        archive_dir = Path(settings.archive_dir)
        archive_dir.mkdir(exist_ok=True)
        src = Path(path)
        dst = archive_dir / src.name
        src.rename(dst)
