import google.generativeai as genai
from vlog_capture.infrastructure.settings import settings
from vlog_capture.portability import runtime_directories


def analyze_overall() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError("VLOG_GEMINI_API_KEY is required for MBTI analysis")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    directories = runtime_directories()
    summaries_dir = settings.summary_dir
    output_file = directories.data / "mbti" / "overall_analysis.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(summaries_dir.glob("*.txt"))
    print(f"Found {len(files)} summary files.")

    all_text = ""
    for summary in files:
        content = summary.read_text(encoding="utf-8")
        all_text += f"\n--- File: {summary.name} ---\n{content}\n"

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
