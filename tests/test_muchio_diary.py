import hashlib
import json
from pathlib import Path

import pytest

from scripts import muchio_diary


def test_muchio_extracts_utterances_not_private_metadata() -> None:
    assert (
        muchio_diary.event_line(
            {
                "timestamp": "2026-10-09",
                "payload": {"recognized_text": "こんにちは", "token": "do-not-forward"},
            }
        )
        == "2026-10-09: こんにちは"
    )
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
        json.dumps({"payload": {"message": "こんにちは"}, "pet_id": "secret"}) + "\n",
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


class _Query:
    def __init__(self, client: "_FakeClient") -> None:
        self.client = client
        self.op = ""
        self.rows: list[dict] = []

    def select(self, *_: object) -> "_Query":
        self.op = "select"
        return self

    def eq(self, *_: object) -> "_Query":
        return self

    def upsert(self, rows: list[dict], on_conflict: str) -> "_Query":
        self.op = "upsert"
        self.client.upserted.extend(rows)
        self.rows = rows
        return self

    def execute(self) -> object:
        from types import SimpleNamespace

        if self.op == "select":
            return SimpleNamespace(data=self.client.existing)
        return SimpleNamespace(data=[{**r} for r in self.rows])


class _FakeClient:
    def __init__(self, existing: list[dict]) -> None:
        self.existing = existing
        self.upserted: list[dict] = []

    def table(self, _: str) -> _Query:
        return _Query(self)


def _reviewed(tmp_path: Path, day: str) -> str:
    (tmp_path / f"{day}.md").write_text("reviewed", encoding="utf-8")
    (tmp_path / f"{day}.json").write_text(
        json.dumps({"date": day, "published": False}), encoding="utf-8"
    )
    return muchio_diary.review(tmp_path, day)


def _fake_supabase(monkeypatch: pytest.MonkeyPatch, client: _FakeClient) -> None:
    import supabase
    from vlog_capture.infrastructure.settings import settings

    monkeypatch.setattr(supabase, "create_client", lambda *_: client)
    monkeypatch.setattr(settings, "supabase_url", "http://x", raising=False)
    monkeypatch.setattr(settings, "supabase_service_role_key", "k", raising=False)


def test_publish_coexists_with_non_muchio_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    day = "2026-10-09"
    sha = _reviewed(tmp_path, day)
    client = _FakeClient([{"file_path": f"summaries/{day}.md", "content": "vlog"}])
    _fake_supabase(monkeypatch, client)
    muchio_diary.publish(tmp_path, day, sha)
    assert [r["file_path"] for r in client.upserted] == [f"muchio/{day}"]


def test_publish_refuses_existing_muchio_row_with_different_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    day = "2026-10-09"
    sha = _reviewed(tmp_path, day)
    client = _FakeClient([{"file_path": f"muchio/{day}", "content": "other text"}])
    _fake_supabase(monkeypatch, client)
    with pytest.raises(RuntimeError, match="Muchio"):
        muchio_diary.publish(tmp_path, day, sha)
    assert client.upserted == []


def test_publish_allows_republish_of_identical_muchio_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    day = "2026-10-09"
    sha = _reviewed(tmp_path, day)
    client = _FakeClient([{"file_path": f"muchio/{day}", "content": "reviewed"}])
    _fake_supabase(monkeypatch, client)
    muchio_diary.publish(tmp_path, day, sha)
    assert len(client.upserted) == 1


def test_review_seals_edited_body(tmp_path: Path) -> None:
    day = "2026-10-09"
    target = tmp_path / f"{day}.md"
    target.write_text("edited private draft", encoding="utf-8")
    (tmp_path / f"{day}.json").write_text(
        json.dumps({"date": day, "diary_sha256": "old", "published": False}),
        encoding="utf-8",
    )
    reviewed = muchio_diary.review(tmp_path, day)
    assert reviewed == hashlib.sha256(target.read_bytes()).hexdigest()
    meta = json.loads((tmp_path / f"{day}.json").read_text(encoding="utf-8"))
    assert meta["reviewed_sha256"] == reviewed
    assert meta["published"] is False
