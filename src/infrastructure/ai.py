import json
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai
import torch
from diffusers import DiffusionPipeline

from src.domain.entities import RecordingSession
from src.infrastructure.observability import TraceLogger
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
        self._tracer = TraceLogger()

    def parse_task(self, user_input: str) -> Dict[str, Any]:
        prompt = settings.prompts["jules"]["parse_task"].format(user_input=user_input)
        start_time = time.time()
        response = self._model.generate_content(prompt)
        text = response.text.strip()
        self._tracer.log(
            component="jules_parse_task",
            model=settings.jules_model,
            start_time=start_time,
            input_text=prompt,
            output_text=text,
        )
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
        return json.loads(text)

    def chat(self, history: List[Dict[str, str]], message: str) -> str:
        # Convert simple history to Gemini ContentDict format
        formatted_history = []
        for h in history:
            role = h.get("role", "user")
            content = h.get("content", "")
            formatted_history.append({"role": role, "parts": [content]})
            
        chat = self._model.start_chat(history=formatted_history)
        start_time = time.time()
        response = chat.send_message(message)
        text = response.text
        self._tracer.log(
            component="jules_chat",
            model=settings.jules_model,
            start_time=start_time,
            input_text=message,
            output_text=text,
        )
        return text

    def generate_image_prompt(self, chapter_text: str) -> str:
        template = settings.prompts["jules"]["image_prompt"]
        prompt = template.format(chapter_text=chapter_text[:2000])
        start_time = time.time()
        response = self._model.generate_content(prompt)
        text = ""
        if response.parts:
            text = response.text.strip()
        self._tracer.log(
            component="jules_image_prompt",
            model=settings.jules_model,
            start_time=start_time,
            input_text=prompt,
            output_text=text,
        )
        return text


class ImageGenerator:
    def __init__(self):
        self._pipe = None
        self._tracer = TraceLogger()

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        prompt, negative_prompt = self._extract_prompt(chapter_text)
        self.generate(prompt, negative_prompt, output_path)

    def _extract_prompt(self, chapter_text: str) -> tuple[str, str]:
        jules = JulesClient()
        text = jules.generate_image_prompt(chapter_text)
        for pattern in settings.image_prompt_filters:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
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
        start_time = time.time()
        image = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=settings.image_height,
            width=settings.image_width,
            num_inference_steps=settings.image_num_inference_steps,
            guidance_scale=settings.image_guidance_scale,
            generator=generator,
        ).images[0]
        self._tracer.log(
            component="image_generator",
            model=settings.image_model,
            start_time=start_time,
            input_text=prompt,
            output_text=f"Saved to {output_path}",
            metadata={"seed": seed, "negative_prompt": negative_prompt},
        )
        image.save(output_path)


class Novelizer:
    def __init__(self):
        self._model = None
        self._prompt_template = settings.prompts["novelizer"]["template"]
        self._tracer = TraceLogger()

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
        start_time = time.time()
        response = self._model.generate_content(
            prompt,
            generation_config={"max_output_tokens": settings.novel_max_output_tokens},
        )
        text = response.text.strip()
        self._tracer.log(
            component="novelizer",
            model=settings.novel_model,
            start_time=start_time,
            input_text=prompt,
            output_text=text,
        )
        return text


class Summarizer:
    def __init__(self):
        self._model = None
        self._prompt_template = settings.prompts["summarizer"]["template"]
        self._tracer = TraceLogger()

    def summarize(
        self,
        transcript: str,
        session: RecordingSession | None = None,
        date_str: str | None = None,
        start_time_str: str | None = None,
        end_time_str: str | None = None,
    ) -> str:
        if not self._model:
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.gemini_model)
        if session:
            d = session.start_time.strftime("%Y-%m-%d")
            s = session.start_time.strftime("%H:%M")
            e = (session.end_time or session.start_time).strftime("%H:%M")
        else:
            d = date_str or "Unknown Date"
            s = start_time_str or "00:00"
            e = end_time_str or "00:00"
        prompt = self._prompt_template.format(
            date=d,
            start_time=s,
            end_time=e,
            transcript=transcript.strip(),
        )
        start_time = time.time()
        response = self._model.generate_content(prompt)
        text = response.text.strip()
        self._tracer.log(
            component="summarizer",
            model=settings.gemini_model,
            start_time=start_time,
            input_text=prompt,
            output_text=text,
        )
        return text


class Curator:
    def __init__(self):
        self._model = None
        self._prompt_template = settings.prompts["curator"]["evaluate"]
        self._tracer = TraceLogger()

    def evaluate(self, summary: str, novel: str) -> Dict[str, Any]:
        if not self._model:
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.jules_model)
        prompt = self._prompt_template.format(summary=summary, novel=novel)
        start_time = time.time()
        response = self._model.generate_content(prompt)
        text = response.text.strip()
        self._tracer.log(
            component="curator_evaluate",
            model=settings.jules_model,
            start_time=start_time,
            input_text=prompt,
            output_text=text,
        )
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "faithfulness_score": 0,
                "quality_score": 0,
                "reasoning": f"JSON Parse Error: {text}",
            }
