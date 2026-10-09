"""Generate private Muchio diaries with the existing VLog prompt, then publish reviewed text.

Raw VRCPet logs remain local. Generation and public publication are separate commands.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

TEXT_KEYS = {
    "text", "message", "content", "utterance", "recognized_text", "transcript",
    "speech", "sentence", "word", "heard", "spoken", "phrase", "recognized",
    "pet_utterance", "user_utterance", "recognized_word", "heard_word",
}
TIME_KEYS = ("timestamp", "time", "datetime", "created_at", "recorded_at")
SPEAKER_KEYS = ("speaker", "source", "actor", "role")
DAY_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
CHUNK_LIMIT = 18000
PRIVATE_NOTE = (
    "【VRCPetの二次観測データ】\n"
    "以下は人間の録音全文ではなく、ペットが記録した観測イベントです。"
    "観測されない出来事や相手の気持ちを断定しないでください。"
    "話者・場所が不明なら補完せず、日記内で不明としてください。"
    "記録された事実と感想の推測を区別してください。\n\n"
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _values(record: Any, depth: int = 0) -> list[str]:
    """Select utterances rather than forwarding arbitrary private metadata."""
    if not isinstance(record, dict) or depth > 3:
        return []
    found: list[str] = []
    for key, value in record.items():
        lowered = key.casefold()
        if lowered in TEXT_KEYS:
            if isinstance(value, str) and value.strip():
                found.append(value.strip()[:2000])
            elif isinstance(value, dict):
                found.extend(_values(value, depth + 1))
        elif lowered in {"data", "payload", "event", "detail", "result"}:
            if isinstance(value, dict):
                found.extend(_values(value, depth + 1))
    return found


def event_line(record: dict[str, Any]) -> str | None:
    values = _values(record)
    if not values:
        return None
    time = next(
        (
            str(record[k])[:35]
            for k in TIME_KEYS
            if isinstance(record.get(k), (str, int, float))
        ),
        "",
    )
    speaker = next(
        (str(record[k])[:40] for k in SPEAKER_KEYS if isinstance(record.get(k), str)),
        "",
    )
    prefix = " ".join(s for s in (time, speaker) if s)
    return f"{prefix}: {' / '.join(values)}" if prefix else " / ".join(values)


def parse_log(path: Path) -> tuple[list[str], int, int, str]:
    from vlog_vrcpet.parser import parse_observation

    before = path.stat()
    source = path.read_bytes()
    after = path.stat()
    if before.st_mtime_ns != after.st_mtime_ns or before.st_size != after.st_size:
        raise RuntimeError(f"source changed during read: {path.name}")
    parsed = parse_observation(f"logs/{path.name}", source)
    lines = [line for item in parsed.records if (line := event_line(item))]
    return lines, len(parsed.records), len(parsed.issues), digest(source)


def _chunks(lines: list[str]) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        if size + len(line) + 1 > CHUNK_LIMIT and current:
            chunks.append("\n".join(current))
            current, size = [], 0
        current.append(line)
        size += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def make_diary(lines: list[str], day: str, summarizer: Any) -> str:
    chunks = _chunks(lines)
    if not chunks:
        raise ValueError("No recognized text; cannot generate an evidence-backed diary")
    summaries = [
        summarizer.summarize(PRIVATE_NOTE + chunk, date_str=day)
        for chunk in chunks
    ]
    result = (
        summaries[0]
        if len(summaries) == 1
        else summarizer.summarize(
            PRIVATE_NOTE + "【同日の分割要約。重複をまとめた日記を作成してください】\n"
            + "\n\n".join(summaries),
            date_str=day,
        )
    ).strip()
    if not result:
        raise RuntimeError("Model returned an empty diary")
    return result


def generate(logs: Path, output: Path, date_filter: str | None = None) -> dict[str, int]:
    from vlog_capture.infrastructure.ai import Summarizer
    from vlog_capture.infrastructure.settings import settings

    if not logs.is_dir():
        raise FileNotFoundError(f"VRCPet logs directory not found: {logs}")
    if date_filter:
        date.fromisoformat(date_filter)
    model = None
    report = {"generated": 0, "unchanged": 0, "no_text": 0, "parse_issues": 0}
    prompt_hash = digest(settings.prompts["summarizer"]["template"].encode())
    for path in sorted(logs.glob("*.jsonl")):
        day = path.stem
        if not DAY_PATTERN.fullmatch(day):
            continue
        try:
            date.fromisoformat(day)
        except ValueError:
            continue
        if date_filter and day != date_filter:
            continue
        lines, records, issues, source_hash = parse_log(path)
        target = output / f"{day}.md"
        manifest = output / f"{day}.json"
        if target.is_file() and manifest.is_file():
            previous = json.loads(manifest.read_text(encoding="utf-8"))
            if (
                previous.get("source_sha256") == source_hash
                and previous.get("prompt_sha256") == prompt_hash
                and previous.get("diary_sha256") == digest(target.read_bytes())
            ):
                report["unchanged"] += 1
                continue
        report["parse_issues"] += issues
        if not lines:
            report["no_text"] += 1
            continue
        if model is None:
            model = Summarizer()
        content = make_diary(lines, day, model)
        output.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n", encoding="utf-8")
        manifest.write_text(
            json.dumps(
                {
                    "date": day,
                    "source_sha256": source_hash,
                    "prompt_sha256": prompt_hash,
                    "diary_sha256": digest(target.read_bytes()),
                    "event_count": records,
                    "observed_text_events": len(lines),
                    "parse_issues": issues,
                    "published": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        report["generated"] += 1
    return report


def publish(output: Path, day: str, expected_hash: str) -> str:
    """Publish only an explicitly reviewed diary, never a raw observation."""
    from supabase import create_client
    from vlog_capture.infrastructure.settings import settings

    if not DAY_PATTERN.fullmatch(day):
        raise ValueError("date must be YYYY-MM-DD")
    date.fromisoformat(day)
    target = output / f"{day}.md"
    manifest = output / f"{day}.json"
    content = target.read_bytes()
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    actual = digest(content)
    if (
        actual != expected_hash
        or metadata.get("diary_sha256") != actual
        or metadata.get("date") != day
    ):
        raise ValueError("Diary content or manifest differs from the reviewed hash")
    if not content.strip():
        raise ValueError("Diary is empty")
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("VLOG_SUPABASE_URL and VLOG_SUPABASE_SERVICE_ROLE_KEY required")
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    existing = client.table("daily_entries").select("file_path").eq("date", day).execute()
    other_paths = [
        row.get("file_path")
        for row in (getattr(existing, "data", None) or [])
        if row.get("file_path") != f"muchio/{day}"
    ]
    if other_paths:
        raise RuntimeError("Existing diary on date; merge/review instead of duplicating")
    response = client.table("daily_entries").upsert(
        [
            {
                "file_path": f"muchio/{day}",
                "date": day,
                "title": f"Muchio日記 {day}",
                "content": content.decode("utf-8"),
                "tags": ["muchio", "diary"],
                "is_public": True,
            }
        ],
        on_conflict="file_path",
    ).execute()
    rows = getattr(response, "data", None)
    if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("is_public") is not True:
        raise RuntimeError("Public row upsert could not be verified")
    metadata["published"] = True
    metadata["published_sha256"] = actual
    metadata["published_at"] = datetime.now(timezone.utc).isoformat()
    manifest.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return f"https://kaflog.vercel.app/day/{day}"


def main() -> None:
    from vlog_capture.portability import runtime_directories

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["generate", "publish"])
    parser.add_argument("--logs-dir", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=runtime_directories().data / "muchio_diaries",
    )
    parser.add_argument("--date")
    parser.add_argument("--sha", help="Full SHA-256 digest of the diary text you reviewed")
    args = parser.parse_args()
    if args.action == "generate":
        from scripts.asset_manifest import configured_vrcpet_logs

        source = args.logs_dir or configured_vrcpet_logs()
        if source is None:
            parser.error("Set --logs-dir or configure vrcpet.yaml logs_dir")
        print(json.dumps(generate(source, args.output, args.date), ensure_ascii=False))
    else:
        if not args.date or not args.sha:
            parser.error("publish requires --date and --sha (reviewed content hash)")
        print(publish(args.output, args.date, args.sha))


if __name__ == "__main__":
    main()
