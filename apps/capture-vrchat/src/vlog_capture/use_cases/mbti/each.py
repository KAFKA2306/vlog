import google.generativeai as genai

from vlog_capture.infrastructure.settings import settings
from vlog_capture.portability import runtime_directories


def analyze_mbti() -> None:
    if not settings.gemini_api_key:
        raise RuntimeError("VLOG_GEMINI_API_KEY is required for MBTI analysis")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    summaries_dir = settings.summary_dir
    output_dir = runtime_directories().data / "mbti" / "per_summary"
    output_dir.mkdir(exist_ok=True, parents=True)

    prompt_template = """
以下の全ての文章（日記・要約）だけから、
厳密に以下の3点について判定・分析してください。

1. ○MBTIタイプ(4軸)
2. ○主機能／補助機能
3. ○心理機能の使い方の癖

対象の文章:
{text}
"""

    files = sorted(summaries_dir.glob("*.txt"))
    print(f"Found {len(files)} summary files.")

    for summary_file in files:
        output_file = output_dir / summary_file.name
        if output_file.exists():
            print(f"Skipping {summary_file.name} (already exists)")
            continue

        print(f"Processing {summary_file.name}...")
        text = summary_file.read_text(encoding="utf-8")

        try:
            prompt = prompt_template.format(text=text)
            response = model.generate_content(prompt)
            result = response.text.strip()
            output_file.write_text(result, encoding="utf-8")
            print(f"Saved analysis to {output_file}")
        except Exception as exc:
            print(f"Error processing {summary_file.name}: {exc}")


if __name__ == "__main__":
    analyze_mbti()
