from typing import List

from src.infrastructure.repositories import FileRepository, TaskRepository
from src.infrastructure.settings import settings


class PhotoGapFillerUseCase:
    def __init__(self):
        self._files = FileRepository()
        self._tasks = TaskRepository()

    def execute(self) -> List[str]:
        novel_dir = settings.novel_out_dir
        photo_dir = settings.photo_dir

        if not novel_dir.exists():
            print(f"Novel directory {novel_dir} does not exist.")
            return []

        missing_dates = []
        for novel_path in novel_dir.glob("*.md"):
            # Expect filename format YYYYMMDD.md
            date_str = novel_path.stem
            photo_path = photo_dir / f"{date_str}.png"

            if not photo_path.exists():
                missing_dates.append(date_str)

        if not missing_dates:
            print("No missing photos found.")
            return []

        print(f"Found {len(missing_dates)} missing photos: {missing_dates}")

        created_tasks = []
        for date_str in missing_dates:
            # Check if task already exists (pending or processing) to avoid duplicates
            existing_tasks = self._tasks.list_runnable()
            is_queued = False
            for task in existing_tasks:
                if task["type"] == "generate_photo" and task.get("date") == date_str:
                    is_queued = True
                    break

            if is_queued:
                print(f"Task for {date_str} already queued, skipping.")
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
            print(f"Queued generation task for {date_str}")

        return created_tasks
