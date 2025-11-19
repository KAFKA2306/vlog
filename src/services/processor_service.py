import glob
import os
from datetime import datetime

from src.infrastructure.settings import settings
from src.infrastructure.summarizer import Summarizer
from src.infrastructure.transcriber import Transcriber


def get_latest_recording():
    list_of_files = glob.glob(os.path.join(settings.recording_dir, "*.wav"))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)


def main():
    audio_path = get_latest_recording()
    if not audio_path:
        return

    transcriber = Transcriber()
    text = transcriber.transcribe(audio_path)

    summarizer = Summarizer()
    summary = summarizer.summarize(text)

    date_str = datetime.now().strftime("%Y-%m-%d")
    diary_path = os.path.join(settings.diary_dir, f"{date_str}_vrchat.md")
    os.makedirs(settings.diary_dir, exist_ok=True)

    with open(diary_path, "a", encoding="utf-8") as f:
        f.write(f"\n## Session {datetime.now().strftime('%H:%M')}\n\n")
        f.write(f"{summary}\n\n")
        f.write(f"### Raw Log\n{text}\n")


if __name__ == "__main__":
    main()
