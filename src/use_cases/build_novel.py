import re
from datetime import datetime
from pathlib import Path

from src.domain.interfaces import ImageGeneratorProtocol, NovelizerProtocol
from src.infrastructure.graph_storage import GraphStorage
from src.infrastructure.settings import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
QUEUE_PATH = _PROJECT_ROOT / "data" / "cognee_queue.yaml"


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

    def _fetch_memories(self, summary: str) -> str:
        query = self._build_search_query(summary)
        results = self._graph_storage.search(query, limit=5)
        return self._graph_storage.get_context_string(results)

    def _build_search_query(self, summary: str) -> str:
        first_line = summary.splitlines()[0].strip()
        first_sentence = re.split(r"[。．.!?！？]", first_line, maxsplit=1)[0].strip()
        return first_sentence[:200] or first_line[:200] or summary[:200]
