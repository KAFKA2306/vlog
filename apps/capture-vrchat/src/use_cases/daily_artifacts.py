from __future__ import annotations

import re
from pathlib import Path

from src.domain.entities import RecordingSession
from src.domain.interfaces import (
    DailySummarizerProtocol,
    FileRepositoryProtocol,
    GraphStorageProtocol,
    ImageGeneratorProtocol,
    NovelizerProtocol,
)
from src.infrastructure.daily_state import (
    DailySourceBundle,
    DailyStateStore,
    collect_daily_sources,
    fingerprint_paths,
    fingerprint_text,
)
from src.infrastructure.settings import settings


class DailyArtifactManager:
    def __init__(self, state_store: DailyStateStore | None = None):
        self._state = state_store or DailyStateStore()

    def summary_sources_for_date(self, date_str: str) -> tuple[Path, ...]:
        return collect_daily_sources(date_str).paths

    def refresh_summary(
        self,
        date_str: str,
        summarizer: DailySummarizerProtocol,
        file_repository: FileRepositoryProtocol,
        *,
        source_paths: tuple[Path, ...] | None = None,
        session: RecordingSession | None = None,
        fallback_text: str | None = None,
    ) -> str | None:
        summary_path = settings.summary_dir / f"{date_str}_summary.txt"
        source_bundle = self._resolve_sources(date_str, source_paths, fallback_text)
        state_entry = self._state.get(date_str)

        has_text_input = bool(source_bundle.combined_text.strip())

        if not has_text_input:
            if summary_path.exists():
                existing = summary_path.read_text(encoding="utf-8")
                if existing.strip():
                    self._bootstrap_summary_state(
                        date_str,
                        summary_path,
                        existing,
                        source_bundle.source_hash,
                        source_bundle.paths,
                    )
                    return existing

            self._state.record_empty(
                date_str,
                "no transcript sources"
                if not source_bundle.paths
                else "empty transcript sources",
            )
            return None

        if (
            summary_path.exists()
            and state_entry.get("summary_source_hash") == source_bundle.source_hash
        ):
            return summary_path.read_text(encoding="utf-8")

        if summary_path.exists() and not state_entry.get("summary_source_hash"):
            existing = summary_path.read_text(encoding="utf-8")
            if existing.strip():
                self._bootstrap_summary_state(
                    date_str,
                    summary_path,
                    existing,
                    source_bundle.source_hash,
                    source_bundle.paths,
                )
                return existing

        summary_text = self._summarize_transcript(
            summarizer,
            source_bundle.combined_text,
            date_str,
            session=session,
        )
        if not summary_text.strip():
            self._state.record_empty(date_str, "empty summary output")
            return None

        summary_path.parent.mkdir(parents=True, exist_ok=True)
        file_repository.save_text(str(summary_path), summary_text)
        self._state.record_summary(
            date_str,
            source_paths=source_bundle.paths,
            source_hash=source_bundle.source_hash,
            summary_text=summary_text,
            summary_path=summary_path,
        )
        return summary_text

    def refresh_novel(
        self,
        date_str: str,
        novelizer: NovelizerProtocol,
        image_generator: ImageGeneratorProtocol,
        graph_storage: GraphStorageProtocol | None = None,
    ) -> Path | None:
        summary_path = settings.summary_dir / f"{date_str}_summary.txt"
        if not summary_path.exists():
            return None

        summary_text = summary_path.read_text(encoding="utf-8")
        if not summary_text.strip():
            self._state.record_empty(date_str, "empty summary content")
            return None

        summary_hash = fingerprint_text(summary_text)
        state_entry = self._state.get(date_str)
        novel_path = settings.novel_out_dir / f"{date_str}.md"
        photo_path = settings.photo_dir / f"{date_str}.png"
        past_memories = (
            self._fetch_memories(graph_storage, summary_text) if graph_storage else ""
        )
        context = f"Past Memories:\n{past_memories}\n\n" if past_memories else ""
        context_hash = fingerprint_text(context)

        if novel_path.exists() and photo_path.exists():
            if not state_entry.get("novel_summary_hash"):
                self._state.record_novel(
                    date_str,
                    summary_hash=summary_hash,
                    context_hash=context_hash,
                    chapter_text=novel_path.read_text(encoding="utf-8"),
                    novel_path=novel_path,
                    photo_path=photo_path,
                )
            return novel_path

        if novel_path.exists():
            novel_so_far = novel_path.read_text(encoding="utf-8")
        else:
            novel_so_far = ""
        chapter = novelizer.generate_chapter(summary_text, novel_so_far, context)

        novel_path.parent.mkdir(parents=True, exist_ok=True)
        novel_path.write_text(chapter, encoding="utf-8")

        photo_path.parent.mkdir(parents=True, exist_ok=True)
        image_generator.generate_from_novel(chapter, photo_path)

        self._state.record_novel(
            date_str,
            summary_hash=summary_hash,
            context_hash=context_hash,
            chapter_text=chapter,
            novel_path=novel_path,
            photo_path=photo_path,
        )
        return novel_path

    def _resolve_sources(
        self,
        date_str: str,
        source_paths: tuple[Path, ...] | None,
        fallback_text: str | None,
    ) -> DailySourceBundle:
        if source_paths is not None:
            paths = tuple(Path(path) for path in source_paths)
            if not paths:
                return collect_daily_sources(date_str)
            combined_text = "\n\n".join(
                path.read_text(encoding="utf-8") for path in paths
            )
            return DailySourceBundle(
                paths=paths,
                source_hash=fingerprint_paths(paths),
                combined_text=combined_text,
            )

        bundle = collect_daily_sources(date_str)
        if bundle.paths:
            return bundle

        if fallback_text is None:
            return bundle

        text = fallback_text.strip()
        if not text:
            return bundle

        return DailySourceBundle(
            paths=tuple(),
            source_hash=fingerprint_text(text),
            combined_text=text,
        )

    def _bootstrap_summary_state(
        self,
        date_str: str,
        summary_path: Path,
        summary_text: str,
        source_hash: str,
        source_paths: tuple[Path, ...],
    ) -> None:
        self._state.record_summary(
            date_str,
            source_paths=source_paths,
            source_hash=source_hash,
            summary_text=summary_text,
            summary_path=summary_path,
        )

    def _summarize_transcript(
        self,
        summarizer: DailySummarizerProtocol,
        transcript: str,
        date_str: str,
        *,
        session: RecordingSession | None = None,
    ) -> str:
        if session is not None:
            return summarizer.summarize(transcript, session)
        return summarizer.summarize(transcript, date_str=date_str)

    def _fetch_memories(self, graph_storage: GraphStorageProtocol, summary: str) -> str:
        query = self._build_search_query(summary)
        results = graph_storage.search(query, limit=5)
        return graph_storage.get_context_string(results)

    def _build_search_query(self, summary: str) -> str:
        first_line = summary.splitlines()[0].strip()
        first_sentence = re.split(r"[。．.!?！？]", first_line, maxsplit=1)[0].strip()
        return first_sentence[:200] or first_line[:200] or summary[:200]
