from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from src.infrastructure.settings import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_STATE_PATH = _PROJECT_ROOT / "data" / "daily_state.json"


def fingerprint_text(text: str) -> str:
    digest = sha256()
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def fingerprint_paths(paths: Iterable[Path]) -> str:
    digest = sha256()
    for path in sorted((Path(p) for p in paths), key=lambda p: p.as_posix()):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True)
class DailySourceBundle:
    paths: tuple[Path, ...]
    source_hash: str
    combined_text: str


class DailyStateStore:
    def __init__(self, path: Path | None = None):
        self._path = path or DEFAULT_STATE_PATH

    def load(self) -> dict:
        if not self._path.exists():
            return {"version": 1, "dates": {}}

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"version": 1, "dates": {}}

        if not isinstance(payload, dict):
            return {"version": 1, "dates": {}}

        payload.setdefault("version", 1)
        payload.setdefault("dates", {})
        return payload

    def save(self, payload: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        tmp_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(self._path)

    def get(self, date_str: str) -> dict:
        data = self.load()
        dates = data.get("dates", {})
        if not isinstance(dates, dict):
            return {}
        entry = dates.get(date_str, {})
        return entry if isinstance(entry, dict) else {}

    def record_summary(
        self,
        date_str: str,
        *,
        source_paths: Iterable[Path],
        source_hash: str,
        summary_text: str,
        summary_path: Path,
    ) -> dict:
        payload = self.load()
        dates = payload.setdefault("dates", {})
        entry = dates.setdefault(date_str, {})
        entry.update(
            {
                "status": "summary_ready",
                "summary_path": str(summary_path),
                "summary_hash": fingerprint_text(summary_text),
                "summary_source_hash": source_hash,
                "summary_source_files": [
                    Path(path).name
                    for path in sorted(source_paths, key=lambda p: Path(p).as_posix())
                ],
                "summary_updated_at": _utc_now(),
            }
        )
        entry.pop("empty_reason", None)
        payload["dates"] = dates
        self.save(payload)
        return entry

    def record_novel(
        self,
        date_str: str,
        *,
        summary_hash: str,
        context_hash: str,
        chapter_text: str,
        novel_path: Path,
        photo_path: Path,
    ) -> dict:
        payload = self.load()
        dates = payload.setdefault("dates", {})
        entry = dates.setdefault(date_str, {})
        entry.update(
            {
                "status": "novel_ready",
                "novel_path": str(novel_path),
                "photo_path": str(photo_path),
                "novel_hash": fingerprint_text(chapter_text),
                "novel_summary_hash": summary_hash,
                "novel_context_hash": context_hash,
                "novel_updated_at": _utc_now(),
            }
        )
        payload["dates"] = dates
        self.save(payload)
        return entry

    def record_empty(self, date_str: str, reason: str) -> dict:
        payload = self.load()
        dates = payload.setdefault("dates", {})
        entry = dates.setdefault(date_str, {})
        entry.update(
            {
                "status": "empty",
                "empty_reason": reason,
                "updated_at": _utc_now(),
            }
        )
        payload["dates"] = dates
        self.save(payload)
        return entry


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def collect_daily_sources(date_str: str) -> DailySourceBundle:
    cleaned = sorted(settings.transcript_dir.glob(f"cleaned_{date_str}_*.txt"))
    sources = cleaned or sorted(settings.transcript_dir.glob(f"{date_str}_*.txt"))
    if not sources:
        return DailySourceBundle(paths=tuple(), source_hash="", combined_text="")

    combined_text = "\n\n".join(path.read_text(encoding="utf-8") for path in sources)
    return DailySourceBundle(
        paths=tuple(sources),
        source_hash=fingerprint_paths(sources),
        combined_text=combined_text,
    )
