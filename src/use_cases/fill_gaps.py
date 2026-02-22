from src.infrastructure.repositories import FileRepository, TaskRepository
from src.infrastructure.settings import settings


class PhotoGapFillerUseCase:
    def __init__(self):
        self._files = FileRepository()
        self._tasks = TaskRepository()

    def execute(self) -> list[str]:
        novel_dir = settings.novel_out_dir
        photo_dir = settings.photo_dir
        if not novel_dir.exists():
            return []

        missing_dates = []
        for novel_path in novel_dir.glob("*.md"):
            date_str = novel_path.stem
            if not (photo_dir / f"{date_str}.png").exists():
                missing_dates.append(date_str)

        if not missing_dates:
            return []

        created_tasks = []
        runnable = self._tasks.list_runnable()
        for date_str in missing_dates:
            if any(
                t["type"] == "generate_photo" and t.get("date") == date_str
                for t in runnable
            ):
                continue
            self._tasks.add(
                {
                    "type": "generate_photo",
                    "date": date_str,
                    "novel_path": str(novel_dir / f"{date_str}.md"),
                    "photo_path": str(photo_dir / f"{date_str}.png"),
                }
            )
            created_tasks.append(date_str)
        return created_tasks
