import json
from pathlib import Path

import pytest

from scripts import nikki_local


def _write_day(logs: Path, day: str, records: list[dict]) -> None:
    logs.mkdir(parents=True, exist_ok=True)
    (logs / f"{day}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def test_transcript_keeps_order_and_speaker_labels() -> None:
    records = [
        {"t": "heard", "text": "おはよう", "ts": 1.0, "words": []},
        {"t": "said", "lines": ["ねむい"], "kind": "idle", "ts": 2.0, "word": None},
        {"t": "event", "name": "chorus", "ts": 3.0},
    ]
    text = nikki_local.build_transcript(records)
    assert text == "あなた: おはよう\nムチォ: ねむい\n［chorus］"


def test_transcript_is_capped_and_reports_truncation() -> None:
    records = [{"t": "heard", "text": "x" * 500, "ts": 1.0, "words": []}] * 40
    text, truncated = nikki_local.build_transcript_capped(records, limit=1000)
    assert len(text) <= 1000
    assert truncated is True


def test_endpoint_must_be_loopback() -> None:
    with pytest.raises(ValueError, match="loopback"):
        nikki_local.require_local_endpoint("http://203.0.113.5:11434/api/generate")
    nikki_local.require_local_endpoint("http://127.0.0.1:11434/api/generate")


def test_output_is_under_ignored_data_private(tmp_path: Path) -> None:
    out = nikki_local.private_output_dir()
    repo = Path(nikki_local.__file__).resolve().parents[1]
    assert out == repo / "data" / "private" / "nikki"


def test_generation_is_idempotent_and_marks_drafts(tmp_path: Path, monkeypatch) -> None:
    logs = tmp_path / "logs"
    _write_day(
        logs,
        "2026-08-11",
        [{"t": "heard", "text": "こんにちは", "ts": 1.0, "words": []}],
    )
    out_dir = tmp_path / "private" / "nikki"
    calls: list[str] = []

    def fake_generate(prompt: str) -> str:
        calls.append(prompt)
        return "今日は挨拶から始まった。"

    first = nikki_local.generate_days(logs, out_dir, generate=fake_generate)
    second = nikki_local.generate_days(logs, out_dir, generate=fake_generate)
    assert first == ["2026-08-11"]
    assert second == []
    assert len(calls) == 1
    body = (out_dir / "2026-08-11.md").read_text(encoding="utf-8")
    assert "非公開の下書き" in body
    assert "今日は挨拶から始まった。" in body


def test_template_is_the_project_summarizer_prompt() -> None:
    template = nikki_local.load_template()
    assert "【YYYY-MM-DD 日記】" in template
    assert "{transcript}" in template and "{date}" in template
