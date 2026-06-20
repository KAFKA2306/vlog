from pathlib import Path

from src.infrastructure.daily_state import DailyStateStore
from src.infrastructure.repositories import FileRepository
from src.infrastructure.settings import settings
from src.use_cases.daily_artifacts import DailyArtifactManager


class StubSummarizer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def summarize(
        self,
        transcript: str,
        session=None,
        date_str=None,
        start_time_str=None,
        end_time_str=None,
    ) -> str:
        self.calls.append(transcript)
        return f"summary-{len(self.calls)}"


class StubNovelizer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def generate_chapter(
        self, today_summary: str, novel_so_far: str = "", context: str = ""
    ) -> str:
        self.calls.append((today_summary, novel_so_far, context))
        return f"chapter-{len(self.calls)}"


class StubImageGenerator:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        self.calls.append(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(chapter_text, encoding="utf-8")


class StubGraphStorage:
    def search(self, query: str, limit: int = 5):
        return []

    def get_context_string(self, results) -> str:
        return ""


class MutableGraphStorage:
    def __init__(self, context_text: str):
        self.context_text = context_text

    def search(self, query: str, limit: int = 5):
        return ["memory"]

    def get_context_string(self, results) -> str:
        return self.context_text


def _patch_settings(monkeypatch, tmp_path):
    transcript_dir = tmp_path / "transcripts"
    summary_dir = tmp_path / "summaries"
    novel_dir = tmp_path / "novels"
    photo_dir = tmp_path / "photos"

    transcript_dir.mkdir()
    summary_dir.mkdir()
    novel_dir.mkdir()
    photo_dir.mkdir()

    monkeypatch.setattr(settings, "transcript_dir", transcript_dir)
    monkeypatch.setattr(settings, "summary_dir", summary_dir)
    monkeypatch.setattr(settings, "novel_out_dir", novel_dir)
    monkeypatch.setattr(settings, "photo_dir", photo_dir)


def test_refresh_summary_skips_when_sources_unchanged(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    state = DailyStateStore(tmp_path / "daily_state.json")
    manager = DailyArtifactManager(state)
    summarizer = StubSummarizer()
    file_repo = FileRepository()

    source = settings.transcript_dir / "cleaned_20260620_000001.txt"
    source.write_text("alpha", encoding="utf-8")

    first = manager.refresh_summary(
        "20260620",
        summarizer,
        file_repo,
        source_paths=(source,),
    )
    second = manager.refresh_summary(
        "20260620",
        summarizer,
        file_repo,
        source_paths=(source,),
    )

    assert first == "summary-1"
    assert second == "summary-1"
    assert len(summarizer.calls) == 1


def test_refresh_summary_rebuilds_when_sources_change(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    state = DailyStateStore(tmp_path / "daily_state.json")
    manager = DailyArtifactManager(state)
    summarizer = StubSummarizer()
    file_repo = FileRepository()

    source_a = settings.transcript_dir / "cleaned_20260620_000001.txt"
    source_b = settings.transcript_dir / "cleaned_20260620_000002.txt"
    source_a.write_text("alpha", encoding="utf-8")

    manager.refresh_summary(
        "20260620",
        summarizer,
        file_repo,
        source_paths=(source_a,),
    )
    source_b.write_text("beta", encoding="utf-8")

    refreshed = manager.refresh_summary(
        "20260620",
        summarizer,
        file_repo,
        source_paths=(source_a, source_b),
    )

    assert refreshed == "summary-2"
    assert len(summarizer.calls) == 2
    assert (settings.summary_dir / "20260620_summary.txt").read_text(encoding="utf-8")


def test_refresh_novel_skips_when_summary_unchanged(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    state = DailyStateStore(tmp_path / "daily_state.json")
    manager = DailyArtifactManager(state)
    novelizer = StubNovelizer()
    image_generator = StubImageGenerator()

    summary_path = settings.summary_dir / "20260620_summary.txt"
    summary_path.write_text("summary body", encoding="utf-8")

    first = manager.refresh_novel(
        "20260620",
        novelizer,
        image_generator,
        StubGraphStorage(),
    )
    second = manager.refresh_novel(
        "20260620",
        novelizer,
        image_generator,
        StubGraphStorage(),
    )

    assert first == settings.novel_out_dir / "20260620.md"
    assert second == settings.novel_out_dir / "20260620.md"
    assert len(novelizer.calls) == 1
    assert (
        settings.novel_out_dir / "20260620.md"
    ).read_text(encoding="utf-8") == "chapter-1"


def test_refresh_novel_skips_empty_summary(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    state = DailyStateStore(tmp_path / "daily_state.json")
    manager = DailyArtifactManager(state)
    novelizer = StubNovelizer()
    image_generator = StubImageGenerator()

    summary_path = settings.summary_dir / "20260620_summary.txt"
    summary_path.write_text("   ", encoding="utf-8")

    result = manager.refresh_novel(
        "20260620",
        novelizer,
        image_generator,
        StubGraphStorage(),
    )

    assert result is None
    assert len(novelizer.calls) == 0


def test_refresh_novel_rebuilds_when_context_changes(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    state = DailyStateStore(tmp_path / "daily_state.json")
    manager = DailyArtifactManager(state)
    novelizer = StubNovelizer()
    image_generator = StubImageGenerator()
    graph_storage = MutableGraphStorage("Past Memories:\nalpha\n\n")

    summary_path = settings.summary_dir / "20260620_summary.txt"
    summary_path.write_text("summary body", encoding="utf-8")

    first = manager.refresh_novel(
        "20260620",
        novelizer,
        image_generator,
        graph_storage,
    )
    graph_storage.context_text = "Past Memories:\nbeta\n\n"
    second = manager.refresh_novel(
        "20260620",
        novelizer,
        image_generator,
        graph_storage,
    )

    assert first == settings.novel_out_dir / "20260620.md"
    assert second == settings.novel_out_dir / "20260620.md"
    assert len(novelizer.calls) == 2
