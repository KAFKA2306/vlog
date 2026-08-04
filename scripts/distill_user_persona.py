import subprocess
from pathlib import Path

import google.generativeai as genai
from src.infrastructure.settings import settings


def distill():
    summary_dir = Path("data/summaries")
    summaries = sorted(summary_dir.glob("*.txt"))
    if not summaries:
        return

    all_text = ""
    for f in summaries:
        all_text += f.read_text(encoding="utf-8") + "\n---\n"

    p_root = Path("colleague-skill/prompts/celebrity")
    analyzer_prompt = (p_root / "persona_analyzer.md").read_text(encoding="utf-8")
    builder_prompt = (p_root / "persona_builder.md").read_text(encoding="utf-8")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    # Step 1: Persona Analysis
    analysis_input = f"{analyzer_prompt}\n\n原材料:\n{all_text[:30000]}"
    analysis_res = model.generate_content(analysis_input)
    analysis_text = analysis_res.text

    import time

    print("Waiting for quota...")
    time.sleep(30)

    # Step 2: Build Persona.md content
    build_input = f"{builder_prompt}\n\n分析結果:\n{analysis_text}"
    build_res = model.generate_content(build_input)
    persona_md = build_res.text

    # Step 3: Create Skill using skill_writer.py
    temp_persona = Path("data/temp_persona.md")
    temp_persona.write_text(persona_md, encoding="utf-8")

    meta_json = Path("data/temp_meta.json")
    meta_json_content = '{"display_name": "VLog User", "character": "celebrity"}'
    meta_json.write_text(meta_json_content, encoding="utf-8")

    subprocess.run(
        [
            "python3",
            "colleague-skill/tools/skill_writer.py",
            "--action",
            "create",
            "--slug",
            "vlog_user",
            "--name",
            "VLog User",
            "--character",
            "celebrity",
            "--persona",
            str(temp_persona),
            "--meta",
            str(meta_json),
            "--base-dir",
            "data/skills",
        ],
        check=True,
    )

    temp_persona.unlink()
    meta_json.unlink()


if __name__ == "__main__":
    distill()
