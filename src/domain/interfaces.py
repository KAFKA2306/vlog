from pathlib import Path
from typing import Mapping, Protocol, Sequence

from src.domain.entities import RecordingSession


class TranscriberProtocol(Protocol):
    def transcribe_and_save(self, audio_path: str) -> tuple[str, str]: ...
    def unload(self) -> None: ...


class TranscriptPreprocessorProtocol(Protocol):
    def process(self, text: str) -> str: ...


class SummarizerProtocol(Protocol):
    def summarize(self, transcript: str, session: RecordingSession) -> str: ...


class DailySummarizerProtocol(Protocol):
    def summarize(
        self,
        transcript: str,
        session: RecordingSession | None = None,
        date_str: str | None = None,
        start_time_str: str | None = None,
        end_time_str: str | None = None,
    ) -> str: ...


class GraphStorageProtocol(Protocol):
    def search(self, query: str, limit: int = 10) -> Sequence[Mapping[str, object]]: ...

    def get_context_string(self, triples: Sequence[Mapping[str, object]]) -> str: ...


class StorageProtocol(Protocol):
    def sync(self) -> None: ...


class FileRepositoryProtocol(Protocol):
    def exists(self, path: str) -> bool: ...
    def save_text(self, path: str, content: str) -> None: ...
    def archive(self, path: str) -> None: ...


class NovelizerProtocol(Protocol):
    def generate_chapter(
        self, today_summary: str, novel_so_far: str = "", context: str = ""
    ) -> str: ...


class ImageGeneratorProtocol(Protocol):
    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None: ...
