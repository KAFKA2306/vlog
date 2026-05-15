import json
import re
from pathlib import Path

# Paths
VAULT_DB = Path("/home/kafka/projects/prompt-vault/db/prompts.json")
VLOG_PROMPTS = Path("data/prompts.yaml")


def sync():
    if not VAULT_DB.exists():
        print(f"Error: Vault DB not found at {VAULT_DB}")
        return

    with open(VAULT_DB, "r", encoding="utf-8") as f:
        vault = json.load(f)

    blocks = {b["id"]: b for b in vault["blocks"]}

    # Extract core Kafka and Style blocks
    character_kafka_content = blocks.get("character_kafka", {}).get("content", "")
    identity_lock_content = blocks.get("kafka_identity_lock", {}).get("content", "")
    lighting_style = blocks.get("master_style_lighting", {}).get("content", "")
    composition_style = blocks.get("master_style_composition", {}).get("content", "")

    if not character_kafka_content:
        print("Error: character_kafka not found in vault")
        return

    # Load existing vlog prompts
    if not VLOG_PROMPTS.exists():
        print(f"Error: Vlog prompts not found at {VLOG_PROMPTS}")
        return

    with open(VLOG_PROMPTS, "r", encoding="utf-8") as f:
        vlog_text = f.read()

    # 1. Update CHARACTER IDENTITY section in jules.image_prompt
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

    # 2. Update STYLE section in jules.image_prompt
    style_pattern = r"(STYLE \(fixed, always apply\):).*?(\n\s+OUTPUT RULES:)"

    # Extract existing base style but ensure our vault-provided masters are present
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

    # 3. Update character_kafka definition in manga_script
    manga_pattern = r"(【かふか キャラクター定義（全コマ固定）】\n\s+外見: ).*?(\n\s+服装: )"
    vlog_text = re.sub(
        manga_pattern,
        r"\1" + character_kafka_content + r"\2",
        vlog_text,
        flags=re.DOTALL,
    )

    # 4. Global Negative Prompt strengthening
    vlog_text = vlog_text.replace(
        "realistic human face,",
        (
            "realistic human face, hyper-realistic, 3d render, "
            "cgi, octane render, unreal engine,"
        ),
    )

    with open(VLOG_PROMPTS, "w", encoding="utf-8") as f:
        f.write(vlog_text)

    print("✅ Kafka identity and Style Lock successfully integrated from prompt-vault.")


if __name__ == "__main__":
    sync()
