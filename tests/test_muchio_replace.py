import json
from pathlib import Path

import pytest

from scripts import muchio_diary, nikki_local
from tests.test_muchio_diary import _fake_supabase, _FakeClient, _Query, _reviewed

DAY = "2026-10-09"


def _existing(muchio: str) -> list[dict]:
    return [
        {"file_path": f"muchio/{DAY}", "content": muchio},
        {"file_path": f"summaries/{DAY}.md", "content": "vlog"},
    ]


def test_replace_updates_only_the_muchio_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sha = _reviewed(tmp_path, DAY)
    client = _FakeClient(_existing("old voice"))
    _fake_supabase(monkeypatch, client)
    muchio_diary.publish(tmp_path, DAY, sha, replace=True)
    assert [r["file_path"] for r in client.upserted] == [f"muchio/{DAY}"]
    assert client.upserted[0]["content"] == "reviewed"


def test_replace_refuses_when_non_muchio_row_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sha = _reviewed(tmp_path, DAY)
    client = _FakeClient(_existing("old voice"))
    _fake_supabase(monkeypatch, client)
    original_execute = _Query.execute

    def execute(self: _Query) -> object:
        result = original_execute(self)
        if self.op == "upsert":
            self.client.existing = [
                {"file_path": f"muchio/{DAY}", "content": "reviewed"},
                {"file_path": f"summaries/{DAY}.md", "content": "tampered"},
            ]
        return result

    monkeypatch.setattr(_Query, "execute", execute)
    with pytest.raises(RuntimeError, match="non-Muchio"):
        muchio_diary.publish(tmp_path, DAY, sha, replace=True)


def test_default_publish_still_refuses_different_muchio_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sha = _reviewed(tmp_path, DAY)
    client = _FakeClient(_existing("old voice"))
    _fake_supabase(monkeypatch, client)
    with pytest.raises(RuntimeError, match="Muchio"):
        muchio_diary.publish(tmp_path, DAY, sha)
    assert client.upserted == []


@pytest.mark.parametrize(
    "body",
    [
        f"{nikki_local.DRAFT_HEADER}\n本文",
        f"# {DAY}\n\n本文",
    ],
)
def test_publish_refuses_draft_header_or_date_heading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    (tmp_path / f"{DAY}.md").write_text(body, encoding="utf-8")
    (tmp_path / f"{DAY}.json").write_text(
        json.dumps({"date": DAY, "published": False}), encoding="utf-8"
    )
    sha = muchio_diary.review(tmp_path, DAY)
    client = _FakeClient([])
    _fake_supabase(monkeypatch, client)
    with pytest.raises(ValueError, match="draft"):
        muchio_diary.publish(tmp_path, DAY, sha, replace=True)
    assert client.upserted == []


def test_local_generation_uses_muchio_diary_and_never_the_summarizer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import vlog_capture.infrastructure.ai as ai

    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError("Summarizer path must not be used")

    monkeypatch.setattr(ai, "Summarizer", forbidden)
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / f"{DAY}.jsonl").write_text(
        json.dumps({"t": "heard", "text": "こんにちは", "ts": 1.0, "words": []}) + "\n",
        encoding="utf-8",
    )
    prompts: list[str] = []
    nikki_local.generate_days(
        logs, tmp_path / "out", generate=lambda p: prompts.append(p) or "本文"
    )
    assert prompts[0].count("【今日の一言】") >= 1
    assert "こんにちは" in prompts[0]
    assert (
        nikki_local.load_template()
        == __import__("yaml").safe_load(
            nikki_local.PROMPTS_PATH.read_text(encoding="utf-8")
        )["muchio_diary"]["template"]
    )


def test_context_window_fits_a_capped_transcript_plus_template(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import urllib.request

    sent: list[dict] = []

    class _Response:
        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"response": "x"}).encode()

    def fake_urlopen(request: urllib.request.Request, timeout: int) -> _Response:
        sent.append(json.loads(request.data))
        return _Response()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    nikki_local.ollama_generate("p")
    assert sent[0]["options"]["num_ctx"] >= 16384
