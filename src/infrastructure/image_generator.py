from pathlib import Path

import google.generativeai as genai
import torch
from diffusers import StableDiffusionXLPipeline

from src.infrastructure.settings import settings


class ImageGenerator:
    def __init__(self):
        self._pipe = None
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.gemini_model)

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        prompt, negative_prompt = self._extract_prompt(chapter_text)
        self.generate(prompt, negative_prompt, output_path)

    def _extract_prompt(self, chapter_text: str) -> tuple[str, str]:
        # Generate optimized prompt using Gemini
        text = self._generate_prompt_from_novel(chapter_text)

        # Read prompts
        base_path = Path(__file__).parent
        template = (
            (base_path / "image_generator_prompt.txt")
            .read_text(encoding="utf-8")
            .strip()
        )
        negative_prompt = (
            (base_path / "image_generator_negative_prompt.txt")
            .read_text(encoding="utf-8")
            .strip()
        )

        return template.format(text=text), negative_prompt

    def _generate_prompt_from_novel(self, chapter_text: str) -> str:
        prompt = f"""
        Analyze the following novel chapter text and generate a concise, English prompt optimized for Stable Diffusion XL (Anime Style).
        Focus on the main character's appearance, the setting, the lighting, and the mood.
        Keep it under 40 words.
        Do not include negative prompts or quality tags (like "best quality").
        
        Novel Text:
        {chapter_text[:2000]}
        
        Output format: Just the comma-separated keywords.
        """
        
        response = self._model.generate_content(prompt)
        return response.text.strip()

    def generate(self, prompt: str, negative_prompt: str, output_path: Path) -> None:
        if not self._pipe:
            self._pipe = StableDiffusionXLPipeline.from_pretrained(
                settings.image_model,
                torch_dtype=torch.bfloat16,
                use_safetensors=True,
                device_map="balanced",
            )

        image = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            height=settings.image_height,
            width=settings.image_width,
            num_inference_steps=settings.image_num_inference_steps,
            guidance_scale=settings.image_guidance_scale,
            generator=torch.Generator("cuda").manual_seed(settings.image_seed),
        ).images[0]

        image.save(output_path)
