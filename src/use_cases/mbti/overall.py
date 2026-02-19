from pathlib import Path

import google.generativeai as genai

from src.infrastructure.settings import settings


def analyze_overall():
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    summaries_dir = Path("data/summaries")
    output_file = Path("data/mbti_overall_analysis.txt")
    files = sorted(list(summaries_dir.glob("*.txt")))
    all_text = "\n".join(f.read_text(encoding="utf-8") for f in files)
    prompt = f"判定・分析してください:1.○MBTIタイプ(4軸) 2.○主機能／補助機能 3.○心理機能の使い方の癖 対象:{all_text}"
    response = model.generate_content(prompt)
    output_file.write_text(response.text.strip(), encoding="utf-8")


if __name__ == "__main__":
    analyze_overall()
