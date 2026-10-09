import hashlib
import json
from pathlib import Path

import pytest

from scripts import muchio_diary


def test_muchio_extracts_utterances_not_private_metadata() -> None:
    assert muchio_diary.event_line(
        {
            "timestamp": "2026-10-09",
            "payload": {"recognized_text": "こんにちは", "token": "do-not-forward"},
        }
    ) == "2026-10-09: こんにちは"
    assert muchio_diary.event_line({"pet_id": "private", "actor": "name"}) is None


def test_muchio_generate_uses_existing_prompt_and_skips_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from vlog_capture.infrastructure import ai

    calls = []

    class FakeSummarizer:
        def summarize(self, transcript: str, date_str: str) -> str:
            calls.append((transcript, date_str))
            return f"【{date_str} 日記】\n観測された言葉を記録"

    monkeypatch.setattr(ai, "Summarizer", FakeSummarizer)
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "2026-10-09.jsonl").write_text(
        json.dumps({"payload": {"message": "こんにちは"}, "pet_id": "secret"})
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "diaries"
    first = muchio_diary.generate(logs, output)
    assert first["generated"] == 1
    assert first["no_text"] == 0
    assert calls and "secret" not in calls[0][0]
    assert (output / "2026-10-09.md").is_file()
    metadata = json.loads((output / "2026-10-09.json").read_text())
    assert metadata["published"] is False
    assert metadata["event_count"] == 1
    second = muchio_diary.generate(logs, output)
    assert second["unchanged"] == 1
    assert len(calls) == 1


def test_publish_refuses_changed_diary_before_network(tmp_path: Path) -> None:
    day = "2026-10-09"
    target = tmp_path / f"{day}.md"
    target.write_text("reviewed", encoding="utf-8")
    sha = hashlib.sha256(target.read_bytes()).hexdigest()
    (tmp_path / f"{day}.json").write_text(
        json.dumps({"date": day, "diary_sha256": sha}), encoding="utf-8"
    )
    target.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        muchio_diary.publish(tmp_path, day, sha)
