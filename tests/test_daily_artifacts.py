from pathlib import Path

from vlog_capture.infrastructure.daily_state import DailyStateStore
from vlog_capture.infrastructure.repositories import FileRepository
from vlog_capture.infrastructure.settings import settings
from vlog_capture.use_cases.daily_artifacts import DailyArtifactManager


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


class StubComedyWriter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def generate_script(
        self, today_summary: str, script_so_far: str = "", context: str = ""
    ) -> str:
        self.calls.append((today_summary, script_so_far, context))
        return f"script-{len(self.calls)}"


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

    def get_context_string(self, triples) -> str:
        return ""


def _patch_settings(monkeypatch, tmp_path):
    transcript_dir = tmp_path / "transcripts"
    summary_dir = tmp_path / "summaries"
    novel_dir = tmp_path / "novels"
    photo_dir = tmp_path / "photos"
    comedy_dir = tmp_path / "comedy"
    comedy_dir.mkdir()
    monkeypatch.setattr(settings, "comedy_out_dir", comedy_dir)

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
    assert (settings.novel_out_dir / "20260620.md").read_text(
        encoding="utf-8"
    ) == "chapter-1"


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


def _comedy_manager(monkeypatch, tmp_path):
    _patch_settings(monkeypatch, tmp_path)
    state = DailyStateStore(tmp_path / "daily_state.json")
    return DailyArtifactManager(state), state


def test_refresh_comedy_generates_and_skips_when_unchanged(monkeypatch, tmp_path):
    manager, state = _comedy_manager(monkeypatch, tmp_path)
    writer = StubComedyWriter()
    (settings.summary_dir / "20260620_summary.txt").write_text(
        "summary body", encoding="utf-8"
    )

    first = manager.refresh_comedy("20260620", writer, StubGraphStorage())
    second = manager.refresh_comedy("20260620", writer, StubGraphStorage())

    assert first == settings.comedy_out_dir / "20260620.md"
    assert second == first
    assert first.read_text(encoding="utf-8") == "script-1"
    assert len(writer.calls) == 1
    entry = state.get("20260620")
    assert entry["comedy_summary_hash"]
    assert "comedy_context_hash" in entry
    assert entry["comedy_path"] == str(first)


def test_refresh_comedy_regenerates_only_comedy_when_summary_changes(
    monkeypatch, tmp_path
):
    manager, state = _comedy_manager(monkeypatch, tmp_path)
    writer = StubComedyWriter()
    novelizer = StubNovelizer()
    summary_path = settings.summary_dir / "20260620_summary.txt"
    summary_path.write_text("summary one", encoding="utf-8")
    manager.refresh_novel(
        "20260620", novelizer, StubImageGenerator(), StubGraphStorage()
    )
    manager.refresh_comedy("20260620", writer, StubGraphStorage())
    novel_hash = state.get("20260620")["novel_summary_hash"]

    summary_path.write_text("summary two", encoding="utf-8")
    manager.refresh_comedy("20260620", writer, StubGraphStorage())

    assert len(writer.calls) == 2
    assert writer.calls[1] == ("summary two", "", "")
    assert (settings.comedy_out_dir / "20260620.md").read_text(
        encoding="utf-8"
    ) == "script-2"
    assert len(novelizer.calls) == 1
    assert state.get("20260620")["novel_summary_hash"] == novel_hash


def test_refresh_comedy_does_not_read_novel_file(monkeypatch, tmp_path):
    manager, _ = _comedy_manager(monkeypatch, tmp_path)
    writer = StubComedyWriter()
    (settings.summary_dir / "20260620_summary.txt").write_text(
        "summary body", encoding="utf-8"
    )
    (settings.novel_out_dir / "20260620.md").write_text("NOVEL", encoding="utf-8")

    manager.refresh_comedy("20260620", writer, StubGraphStorage())

    assert "NOVEL" not in "".join(writer.calls[0])


def test_refresh_comedy_skips_empty_or_missing_summary(monkeypatch, tmp_path):
    manager, _ = _comedy_manager(monkeypatch, tmp_path)
    writer = StubComedyWriter()

    assert manager.refresh_comedy("20260620", writer, StubGraphStorage()) is None
    (settings.summary_dir / "20260620_summary.txt").write_text("   ", encoding="utf-8")
    assert manager.refresh_comedy("20260620", writer, StubGraphStorage()) is None
    assert len(writer.calls) == 0
