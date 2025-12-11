import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai
import torch
from diffusers import DiffusionPipeline

from src.domain.entities import RecordingSession
from src.infrastructure.settings import settings


class JulesClient:
    def __init__(self):
        jules_key = settings.jules_api_key
        gemini_key = settings.gemini_api_key

        api_key = None
        if jules_key and jules_key.startswith("AIza"):
            api_key = jules_key
        elif gemini_key and gemini_key.startswith("AIza"):
            api_key = gemini_key
        else:
            api_key = jules_key or gemini_key

        if not api_key:
            raise ValueError("Neither GOOGLE_JULES_API_KEY nor GOOGLE_API_KEY is set")

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(settings.jules_model)

    def parse_task(self, user_input: str) -> Dict[str, Any]:
        prompt = settings.prompts["jules"]["parse_task"].format(user_input=user_input)

        response = self._model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
        return json.loads(text)

    def chat(self, history: List[Dict[str, str]], message: str) -> str:
        chat = self._model.start_chat(history=history)
        response = chat.send_message(message)
        return response.text

    def generate_image_prompt(self, chapter_text: str) -> str:
        template = settings.prompts["jules"]["image_prompt"]
        prompt = template.format(chapter_text=chapter_text[:2000])

        response = self._model.generate_content(prompt)
        return response.text.strip()


class ImageGenerator:
    def __init__(self):
        self._pipe = None

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        prompt, negative_prompt = self._extract_prompt(chapter_text)
        self.generate(prompt, negative_prompt, output_path)

    def _extract_prompt(self, chapter_text: str) -> tuple[str, str]:
        jules = JulesClient()
        text = jules.generate_image_prompt(chapter_text)

        text = re.sub(
            r"\b(pig|swine|hog|boar|piglet)s?\b", "", text, flags=re.IGNORECASE
        )
        text = re.sub(
            r"\b(translucent|transparent|semi-transparent|ethereal)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )

        template = settings.prompts["image_generator"]["template"]
        negative_prompt = settings.prompts["image_generator"]["negative_prompt"]

        return template.format(text=text), negative_prompt

    def generate(
        self, prompt: str, negative_prompt: str, output_path: Path, seed: int = None
    ) -> None:
        if not self._pipe:
            self._pipe = DiffusionPipeline.from_pretrained(
                settings.image_model,
                torch_dtype=torch.bfloat16,
                use_safetensors=True,
                device_map="balanced",
            )

        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        print(f"Generating image with seed: {seed}")

        generator = torch.Generator(settings.image_device).manual_seed(seed)

        prompt_path = settings.photo_prompt_dir / f"{output_path.stem}.txt"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(
            f"Prompt:\n{prompt}\n\nNegative Prompt:\n{negative_prompt}",
            encoding="utf-8",
        )

        image = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=settings.image_height,
            width=settings.image_width,
            num_inference_steps=settings.image_num_inference_steps,
            guidance_scale=settings.image_guidance_scale,
            generator=generator,
        ).images[0]

        image.save(output_path)


class Novelizer:
    def __init__(self):
        self._model = None
        self._prompt_template = settings.prompts["novelizer"]["template"]

    def generate_chapter(
        self,
        today_summary: str,
        novel_so_far: str = "",
    ) -> str:
        if not self._model:
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.novel_model)

        prompt = self._prompt_template.format(
            novel_so_far=novel_so_far,
            today_summary=today_summary,
        )

        response = self._model.generate_content(
            prompt,
            generation_config={"max_output_tokens": settings.novel_max_output_tokens},
        )
        return response.text.strip()


class Summarizer:
    def __init__(self):
        self._model = None
        self._prompt_template = settings.prompts["summarizer"]["template"]

    def summarize(self, transcript: str, session: RecordingSession) -> str:
        if not self._model:
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.gemini_model)

        prompt = self._prompt_template.format(
            date=session.start_time.strftime("%Y-%m-%d"),
            start_time=session.start_time.strftime("%H:%M"),
            end_time=(session.end_time or session.start_time).strftime("%H:%M"),
            transcript=transcript.strip(),
        )
        response = self._model.generate_content(prompt)
        return response.text.strip()
