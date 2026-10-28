from datetime import datetime
from pathlib import Path

from vlog_capture.domain.entities import RecordingSession
from vlog_capture.infrastructure.daily_state import DailyStateStore
from vlog_capture.use_cases.daily_artifacts import DailyArtifactManager
from vlog_capture.use_cases.process_recording import ProcessRecordingUseCase

TRANSCRIPT_PATH = "data/transcripts/20260412_120000.txt"


class StubTranscriber:
    def __init__(self, text: str = "", path: str = TRANSCRIPT_PATH):
        self._text = text
        self._path = path
        self.unloaded = False

    def transcribe_and_save(self, audio_path: str) -> tuple[str, str]:
        return self._text, self._path

    def unload(self) -> None:
        self.unloaded = True


class StubPreprocessor:
    def __init__(self, output: str | None = None):
        self._output = output

    def process(self, text: str) -> str:
        return self._output if self._output is not None else text


class StubSummarizer:
    def __init__(self):
        self.called = False

    def summarize(
        self,
        transcript: str,
        session: RecordingSession | None = None,
        date_str: str | None = None,
        start_time_str: str | None = None,
        end_time_str: str | None = None,
    ) -> str:
        self.called = True
        return "summary"


class StubStorage:
    def __init__(self):
        self.synced = False

    def sync(self) -> None:
        self.synced = True


class StubFileRepository:
    def __init__(self):
        self.saved: dict[str, str] = {}
        self.archived: list[str] = []
        self._exists = True

    def exists(self, path: str) -> bool:
        return self._exists

    def save_text(self, path: str, content: str) -> None:
        self.saved[path] = content

    def archive(self, path: str) -> None:
        self.archived.append(path)


class StubNovelizer:
    def __init__(self):
        self.called = False

    def generate_chapter(self, today_summary: str, novel_so_far: str = "") -> str:
        self.called = True
        return "chapter"


class StubImageGenerator:
    def __init__(self):
        self.called = False

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        self.called = True


def _make_usecase(
    transcript_text: str = "",
    preprocessed: str | None = None,
    state_path: Path | None = None,
) -> tuple[
    ProcessRecordingUseCase,
    StubSummarizer,
    StubFileRepository,
    StubStorage,
]:
    transcriber = StubTranscriber(text=transcript_text)
    preprocessor = StubPreprocessor(output=preprocessed)
    summarizer = StubSummarizer()
    storage = StubStorage()
    files = StubFileRepository()
    daily_artifacts = DailyArtifactManager(
        DailyStateStore(state_path) if state_path else None
    )

    uc = ProcessRecordingUseCase(
        transcriber=transcriber,
        preprocessor=preprocessor,
        summarizer=summarizer,
        storage=storage,
        file_repository=files,
        daily_artifacts=daily_artifacts,
    )
    return uc, summarizer, files, storage


class TestTranscriptSizeGate:
    AUDIO_PATH = "data/recordings/20260412_120000.flac"

    def test_execute_skips_when_cleaned_text_too_short(self, tmp_path):
        uc, summarizer, files, storage = _make_usecase(
            preprocessed="あ", state_path=tmp_path / "daily_state.json"
        )
        result = uc.execute(self.AUDIO_PATH, sync=False)

        assert result is False
        assert not summarizer.called
        assert self.AUDIO_PATH in files.archived
        assert not any("cleaned_" in k for k in files.saved)

    def test_execute_skips_when_cleaned_text_empty(self, tmp_path):
        uc, summarizer, files, storage = _make_usecase(
            preprocessed="", state_path=tmp_path / "daily_state.json"
        )
        result = uc.execute(self.AUDIO_PATH, sync=False)

        assert result is False
        assert not summarizer.called
        assert self.AUDIO_PATH in files.archived

    def test_execute_proceeds_when_cleaned_text_sufficient(self, tmp_path):
        long_text = (
            "今日はVRChatでフレンドと一緒にワールド巡りをした。とても楽しい時間だった。"
        )
        uc, summarizer, files, storage = _make_usecase(
            preprocessed=long_text, state_path=tmp_path / "daily_state.json"
        )
        result = uc.execute(self.AUDIO_PATH, sync=False)

        assert result is True
        assert any("cleaned_" in k for k in files.saved)

    def test_execute_does_not_sync_on_skip(self, tmp_path):
        uc, summarizer, files, storage = _make_usecase(
            preprocessed="", state_path=tmp_path / "daily_state.json"
        )
        uc.execute(self.AUDIO_PATH, sync=True)

        assert not storage.synced

    def test_execute_boundary_exactly_50_bytes(self, tmp_path):
        text_50b = "あ" * 16 + "ab"
        assert len(text_50b.encode("utf-8")) == 50
        uc, summarizer, files, _ = _make_usecase(
            preprocessed=text_50b, state_path=tmp_path / "daily_state.json"
        )
        result = uc.execute(self.AUDIO_PATH, sync=False)

        assert result is False
        assert not summarizer.called

    def test_execute_boundary_51_bytes_proceeds(self, tmp_path):
        text_51b = "あ" * 16 + "abc"
        assert len(text_51b.encode("utf-8")) == 51
        uc, summarizer, files, _ = _make_usecase(
            preprocessed=text_51b, state_path=tmp_path / "daily_state.json"
        )
        result = uc.execute(self.AUDIO_PATH, sync=False)

        assert result is True


class TestSessionTranscriptSizeGate:
    def _make_session(self, *paths: str) -> RecordingSession:
        return RecordingSession(
            file_paths=tuple(paths),
            start_time=datetime(2026, 4, 12, 12, 0, 0),
            end_time=datetime(2026, 4, 12, 13, 0, 0),
        )

    def test_execute_session_skips_when_cleaned_text_too_short(self, tmp_path):
        audio = "data/recordings/20260412_120000.flac"
        uc, summarizer, files, _ = _make_usecase(
            preprocessed="あ", state_path=tmp_path / "daily_state.json"
        )
        session = self._make_session(audio)
        result = uc.execute_session(session)

        assert result is False

        assert not summarizer.called
        assert audio in files.archived
        assert not any("cleaned_" in k for k in files.saved)

    def test_execute_session_proceeds_when_sufficient(self, tmp_path):
        audio = "data/recordings/20260412_120000.flac"
        long_text = (
            "今日はVRChatでフレンドと一緒にワールド巡りをした。とても楽しい時間だった。"
        )
        uc, summarizer, files, _ = _make_usecase(
            preprocessed=long_text, state_path=tmp_path / "daily_state.json"
        )
        session = self._make_session(audio)
        result = uc.execute_session(session)

        assert result is True

        assert any("cleaned_" in k for k in files.saved)
        assert audio in files.archived
