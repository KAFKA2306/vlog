import os
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

from src.infrastructure.settings import settings


def analyze_overall():
    load_dotenv()

    if not settings.gemini_api_key:
        print("Error: GOOGLE_API_KEY not found.")
        return

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    summaries_dir = Path("data/summaries")
    output_file = Path("data/mbti_overall_analysis.txt")

    # Read all summary files
    files = sorted(list(summaries_dir.glob("*.txt")))
    print(f"Found {len(files)} summary files.")

    all_text = ""
    for f in files:
        content = f.read_text(encoding="utf-8")
        all_text += f"\n--- File: {f.name} ---\n{content}\n"

    prompt = f"""
以下の全ての文章（日記・要約）だけから、
厳密に以下の3点について判定・分析してください。

1. ○MBTIタイプ(4軸)
2. ○主機能／補助機能
3. ○心理機能の使い方の癖

対象の文章:
{all_text}
"""

    response = model.generate_content(prompt)
    result = response.text.strip()

    output_file.write_text(result, encoding="utf-8")
    print(f"Saved strict overall analysis to {output_file}")


if __name__ == "__main__":
    analyze_overall()
