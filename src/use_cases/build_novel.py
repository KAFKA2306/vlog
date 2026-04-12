import asyncio
from datetime import datetime
from pathlib import Path

from src.domain.interfaces import ImageGeneratorProtocol, NovelizerProtocol
from src.infrastructure.cognee import cognee_memory
from src.infrastructure.settings import settings


class BuildNovelUseCase:
    def __init__(
        self,
        novelizer: NovelizerProtocol,
        image_generator: ImageGeneratorProtocol,
    ):
        self._novelizer = novelizer
        self._image_generator = image_generator

    def execute(self, date: str = None) -> Path | None:
        target_date = date or datetime.now().strftime("%Y%m%d")
        summary_path = settings.summary_dir / f"{target_date}_summary.txt"

        if not summary_path.exists():
            return None

        today_summary = summary_path.read_text(encoding="utf-8")
        novel_path = settings.novel_out_dir / f"{target_date}.md"

        novel_so_far = ""
        if novel_path.exists():
            novel_so_far = novel_path.read_text(encoding="utf-8")

        # Fetch relevant memories from Cognee
        past_memories = self._fetch_memories(today_summary)
        context = f"Past Memories:\n{past_memories}\n\n" if past_memories else ""

        chapter = self._novelizer.generate_chapter(today_summary, novel_so_far, context)
        novel_path.parent.mkdir(parents=True, exist_ok=True)

        if novel_so_far:
            novel_path.write_text(f"{novel_so_far}\n\n{chapter}", encoding="utf-8")
        else:
            novel_path.write_text(chapter, encoding="utf-8")

        photo_path = settings.photo_dir / f"{target_date}.png"
        photo_path.parent.mkdir(parents=True, exist_ok=True)
        self._image_generator.generate_from_novel(chapter, photo_path)

        return novel_path

    def _fetch_memories(self, query: str) -> str:
        """Fetch relevant memories from Cognee based on today's summary."""
        try:
            results = asyncio.run(cognee_memory.search(query))
            if not results:
                return ""

            # Standardize extraction of results based on Cognee 1.0 output structure
            memory_texts = []
            for res in results:
                if isinstance(res, dict) and "search_result" in res:
                    memory_texts.extend(res["search_result"])
                else:
                    memory_texts.append(str(res))

            return "\n---\n".join(memory_texts[:3])  # Top 3 relevant memories
        except Exception as e:
            print(f"Failed to fetch memories: {e}")
            return ""
