import hashlib
from pathlib import Path

import yaml

PROMPTS = Path(__file__).resolve().parents[1] / "data/prompts.yaml"
SUMMARIZER_SHA256 = "1c3c44ce1f50f01b91fcbc7a08b4cc716d5dead6f97a2e602db78ab01044803b"
SAFETY_LINES = (
    "ただし、** や # などの強調記号は一切使用しないでください。見出しには【 】を使用してください。",
    "VR機器（HMD、ヘッドセット、コントローラー、トラッカーなど）への言及は、当たり前の前提であるため禁止します。デバイスではなく、体験そのものを描写してください。",
    "音声認識の誤りは文脈から最も自然な単語に補正し、不自然なまま残さない。",
    "補正はトランスクリプト内で情報に基づく推定のみに留め、新しい出来事を創作しない。",
)
VOICE_MARKERS = ("【文体】", "【笑いの作法】", "【今日の一言】")


def _prompts() -> dict:
    return yaml.safe_load(PROMPTS.read_text(encoding="utf-8"))


def test_muchio_diary_voice_block_exists() -> None:
    template = _prompts()["muchio_diary"]["template"]
    for marker in VOICE_MARKERS:
        assert marker in template


def test_vrchat_summarizer_template_is_unchanged() -> None:
    template = _prompts()["summarizer"]["template"]
    assert hashlib.sha256(template.encode()).hexdigest() == SUMMARIZER_SHA256
    assert "【文体】" not in template


def test_only_muchio_scripts_reference_muchio_diary_prompt() -> None:
    root = PROMPTS.parents[1]
    referencing = {
        path.relative_to(root).as_posix()
        for path in (root / "apps").rglob("*.py")
        if 'prompts["muchio_diary"]' in path.read_text(encoding="utf-8")
    }
    assert referencing == set()


def test_muchio_diary_keeps_safety_lines_and_output_contract() -> None:
    template = _prompts()["muchio_diary"]["template"]
    for line in SAFETY_LINES:
        assert line in template
    assert "【{date} 日記】" in template
    assert "{transcript}" in template
    assert 'tags: ["タグ1", "タグ2", ...]' in template
    assert template.format(date="2000-01-01", transcript="x")
