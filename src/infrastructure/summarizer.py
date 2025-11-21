import os

import google.generativeai as genai

from src.domain.entities import RecordingSession
from src.infrastructure.settings import settings


class Summarizer:
    def __init__(self):
        self._model = None

    def summarize(self, transcript: str, session: RecordingSession) -> str:
        model = self._ensure_model()
        start_ts = session.start_time.strftime("%Y-%m-%d %H:%M")
        end_ts = (session.end_time or session.start_time).strftime("%Y-%m-%d %H:%M")
        prompt = (
            "あなたはVRChatプレイログを短い日記にまとめるアシスタントです。"
            "以下のルールでMarkdownテキストのみを日本語で出力してください。\n"
            "- 箇条書き3〜5個で出来事を要約する\n"
            "- 1〜2行の気づき・次にやりたいことを『気づき』セクションで書く\n"
            "- 実名が含まれていたらイニシャルに置き換える\n"
            "- ない内容は作らない\n\n"
            f"セッション時間: {start_ts} 〜 {end_ts}\n"
            "---\n"
            f"{transcript.strip()}\n"
        )
        response = model.generate_content(prompt)
        return response.text.strip()

    def _ensure_model(self):
        if self._model:
            return self._model
        api_key = settings.gemini_api_key or os.getenv(settings.gemini_api_key_env)
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)
        return self._model
