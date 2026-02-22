import json
import re
from pathlib import Path
from typing import Any, Dict

import google.generativeai as genai
import torch
from diffusers import DiffusionPipeline

from src.infrastructure.observability import TraceLogger
from src.infrastructure.settings import settings


class JulesClient:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.jules_model)

    def generate_image_prompt(self, chapter_text: str) -> str:
        msg = (
            "Extract a visual scene description for an anime illustration "
            f"from this text. Output only the description: {chapter_text}"
        )
        response = self._model.generate_content(msg)
        return response.text.strip()

    def evaluate_novel(self, chapter: str, transcript: str) -> Dict[str, Any]:
        prompt = f"""Evaluate this novel chapter based on the transcript.
Return JSON: {{"faithfulness_score": 0-10, "quality_score": 0-10, "reasoning": "..."}}
Transcript: {transcript}
Chapter: {chapter}"""
        response = self._model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text or "{}")

    def parse_task(self, content: str) -> dict:
        return {"id": "task_id", "title": content, "status": "pending"}


class Summarizer:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.novel_model)
        self._trace = TraceLogger()

    def generate_novel(self, transcript: str, date_str: str) -> str:
        prompt = settings.prompts.get(
            "novel_generation", "Write a novel from this transcript: {transcript}"
        ).format(transcript=transcript)
        response = self._model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=settings.novel_max_output_tokens,
                temperature=0.7,
            ),
        )
        content = response.text.strip()
        self._trace.log(
            "novel_generation",
            {"date": date_str, "transcript_len": len(transcript)},
            content,
        )
        return content


Novelizer = Summarizer


class ImageGenerator:
    def __init__(self):
        self._pipe: Any = None

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        prompt, negative_prompt = self._extract_prompt(chapter_text)
        self.generate(prompt, negative_prompt, output_path)

    def _extract_prompt(self, chapter_text: str) -> tuple[str, str]:
        jules = JulesClient()
        text = jules.generate_image_prompt(chapter_text)
        for pattern in settings.image_prompt_filters:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        prompt = settings.image_generator_default_prompt.format(text=text.strip())
        return prompt, settings.image_generator_default_negative_prompt

    def generate(
        self,
        prompt: str,
        negative_prompt: str,
        output_path: Path,
        seed: int | None = None,
    ) -> None:
        device = settings.image_device
        dtype = torch.bfloat16
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
            dtype = torch.float32

        if not self._pipe:
            self._pipe = DiffusionPipeline.from_pretrained(
                settings.image_model,
                torch_dtype=dtype,
                use_safetensors=True,
            )
            self._pipe.to(device)

        gen = (
            torch.Generator(device=device).manual_seed(seed)
            if seed is not None
            else None
        )
        image = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=settings.image_num_inference_steps,
            guidance_scale=settings.image_guidance_scale,
            height=settings.image_height,
            width=settings.image_width,
            generator=gen,
        ).images[0]
        image.save(output_path)


class Curator:
    def evaluate(self, chapter: str, transcript: str) -> Dict[str, Any]:
        return JulesClient().evaluate_novel(chapter, transcript)
