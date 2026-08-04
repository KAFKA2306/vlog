from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VAULT_DB = Path(
    os.environ.get(
        "PROMPT_VAULT_DB",
        REPO_ROOT.parent / "prompt-vault" / "db" / "prompts.json",
    )
).expanduser()
VLOG_PROMPTS = REPO_ROOT / "data" / "prompts.yaml"


def sync() -> int:
    if not VAULT_DB.exists():
        print(f"Error: Vault DB not found at {VAULT_DB}")
        return 1

    with VAULT_DB.open("r", encoding="utf-8") as stream:
        vault = json.load(stream)

    blocks = {block["id"]: block for block in vault["blocks"]}
    character_kafka_content = blocks.get("character_kafka", {}).get("content", "")
    identity_lock_content = blocks.get("kafka_identity_lock", {}).get("content", "")
    lighting_style = blocks.get("master_style_lighting", {}).get("content", "")
    composition_style = blocks.get("master_style_composition", {}).get("content", "")

    if not character_kafka_content:
        print("Error: character_kafka not found in vault")
        return 1
    if not VLOG_PROMPTS.exists():
        print(f"Error: Vlog prompts not found at {VLOG_PROMPTS}")
        return 1

    vlog_text = VLOG_PROMPTS.read_text(encoding="utf-8")
    identity_pattern = (
        r"(CHARACTER IDENTITY \(always present, never omit\):).*?"
        r"(\n\s+STYLE \(fixed, always apply\):)"
    )
    new_identity = f"""- Kafka: {character_kafka_content}
    - Lock: {identity_lock_content}
    - Consistency: Maintain identical face, hair gradients, and cat accessories across all frames. No photorealism."""
    new_identity_indented = "\n    " + "\n    ".join(new_identity.splitlines())
    vlog_text = re.sub(
        identity_pattern,
        r"\1" + new_identity_indented + r"\2",
        vlog_text,
        flags=re.DOTALL,
    )

    style_pattern = r"(STYLE \(fixed, always apply\):).*?(\n\s+OUTPUT RULES:)"
    new_style = f"""- japanese anime style, soft pastel color palette, clean light background
    - airy, transparent, gentle, dreamy atmosphere
    - {lighting_style}, {composition_style}
    - sharp clean lineart, highly detailed, 4k quality
    - NOT cyberpunk, NOT dark, NOT photorealistic, NOT 3d render, NOT hyper-realistic"""
    new_style_indented = "\n    " + "\n    ".join(new_style.splitlines())
    vlog_text = re.sub(
        style_pattern,
        r"\1" + new_style_indented + r"\2",
        vlog_text,
        flags=re.DOTALL,
    )

    manga_pattern = (
        r"(【かふか キャラクター定義（全コマ固定）】\n\s+外見: ).*?(\n\s+服装: )"
    )
    vlog_text = re.sub(
        manga_pattern,
        r"\1" + character_kafka_content + r"\2",
        vlog_text,
        flags=re.DOTALL,
    )
    vlog_text = vlog_text.replace(
        "realistic human face,",
        "realistic human face, hyper-realistic, 3d render, cgi, octane render, unreal engine,",
    )
    VLOG_PROMPTS.write_text(vlog_text, encoding="utf-8")
    print("Kafka identity and style lock integrated from prompt-vault.")
    return 0


if __name__ == "__main__":
    raise SystemExit(sync())
