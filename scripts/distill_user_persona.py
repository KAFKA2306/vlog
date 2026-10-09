from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import google.generativeai as genai
from vlog_capture.infrastructure.settings import settings
from vlog_capture.portability import runtime_directories
from vlog_capture.project import PROJECT_ROOT

PROMPT_ROOT = PROJECT_ROOT / "colleague-skill" / "prompts" / "celebrity"
SKILL_WRITER = PROJECT_ROOT / "colleague-skill" / "tools" / "skill_writer.py"


def distill() -> None:
    directories = runtime_directories()
    summary_dir = directories.data / "summaries"
    skill_dir = directories.data / "skills"

    summaries = sorted(summary_dir.glob("*.txt"))
    if not summaries:
        return

    all_text = "\n---\n".join(
        summary.read_text(encoding="utf-8") for summary in summaries
    )

    analyzer_prompt = (PROMPT_ROOT / "persona_analyzer.md").read_text(encoding="utf-8")
    builder_prompt = (PROMPT_ROOT / "persona_builder.md").read_text(encoding="utf-8")

    if not settings.gemini_api_key:
        raise RuntimeError("VLOG_GEMINI_API_KEY is required for persona distillation")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    analysis_input = f"{analyzer_prompt}\n\n原材料:\n{all_text[:30000]}"
    analysis_text = model.generate_content(analysis_input).text

    build_input = f"{builder_prompt}\n\n分析結果:\n{analysis_text}"
    persona_md = model.generate_content(build_input).text

    directories.state.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="persona-", dir=directories.state
    ) as temp_directory:
        temp_root = Path(temp_directory)
        temp_persona = temp_root / "persona.md"
        temp_meta = temp_root / "meta.json"
        temp_persona.write_text(persona_md, encoding="utf-8")
        temp_meta.write_text(
            json.dumps(
                {"display_name": "VLog User", "character": "celebrity"},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        subprocess.run(
            [
                sys.executable,
                str(SKILL_WRITER),
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
                str(temp_meta),
                "--base-dir",
                str(skill_dir),
            ],
            check=True,
            cwd=PROJECT_ROOT,
        )


if __name__ == "__main__":
    distill()
