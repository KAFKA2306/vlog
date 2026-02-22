from pathlib import Path

import google.generativeai as genai  # type: ignore
from src.infrastructure.settings import settings


def analyze_mbti():
    genai.configure(api_key=settings.gemini_api_key)  # pyright: ignore[reportPrivateImportUsage]
    model = genai.GenerativeModel(settings.gemini_model)  # pyright: ignore[reportPrivateImportUsage]
    summaries_dir = Path("data/summaries")
    output_dir = Path("data/mbti_analysis")
    output_dir.mkdir(exist_ok=True, parents=True)
    prompt_template = (
        "判定・分析してください:"
        "1.○MBTIタイプ(4軸) 2.○主機能 / 補助機能 3.○心理機能の使い方の癖 "
        "対象:{text}"
    )
    files = sorted(summaries_dir.glob("*.txt"))
    for summary_file in files:
        output_file = output_dir / summary_file.name
        if output_file.exists():
            continue
        text = summary_file.read_text(encoding="utf-8")
        response = model.generate_content(prompt_template.format(text=text))
        output_file.write_text(response.text.strip(), encoding="utf-8")


if __name__ == "__main__":
    analyze_mbti()
