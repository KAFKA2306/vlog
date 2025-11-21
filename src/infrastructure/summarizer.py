import os
from pathlib import Path

import google.generativeai as genai

from src.domain.entities import RecordingSession
from src.infrastructure.settings import settings


class Summarizer:
    def __init__(self):
        self._model = None
        self._prompt_template = (
            Path(__file__)
            .with_name("summarizer_prompt.txt")
            .read_text(encoding="utf-8")
        )

    def summarize(self, transcript: str, session: RecordingSession) -> str:
        model = self._ensure_model()
        start_date = session.start_time.strftime("%Y-%m-%d")
        start_time = session.start_time.strftime("%H:%M")
        end_time = (session.end_time or session.start_time).strftime("%H:%M")
        prompt = self._prompt_template.format(
            date=start_date,
            start_time=start_time,
            end_time=end_time,
            transcript=transcript.strip(),
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
