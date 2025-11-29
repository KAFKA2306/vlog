from pathlib import Path

import torch
from diffusers import ZImagePipeline

from src.infrastructure.settings import settings


class ImageGenerator:
    def __init__(self):
        self._pipe = None

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        prompt, negative_prompt = self._extract_prompt(chapter_text)
        self.generate(prompt, negative_prompt, output_path)

    def _extract_prompt(self, chapter_text: str) -> tuple[str, str]:
        lines = [line.strip() for line in chapter_text.split("\n") if line.strip()]

        # Extract first few meaningful paragraphs (skip headings)
        paragraphs = [
            line for line in lines if len(line) > 20 and not line.startswith("#")
        ][:3]

        if paragraphs:
            text = " ".join(paragraphs)[:500]
        else:
            text = "peaceful atmosphere"

        base_path = Path(__file__).parent
        prompt_path = base_path / "image_generator_prompt.txt"
        negative_prompt_path = base_path / "image_generator_negative_prompt.txt"

        if prompt_path.exists():
            template = prompt_path.read_text(encoding="utf-8").strip()
        else:
            template = settings.image_generator_default_prompt

        if negative_prompt_path.exists():
            negative_prompt = negative_prompt_path.read_text(encoding="utf-8").strip()
        else:
            negative_prompt = settings.image_generator_default_negative_prompt

        return template.format(text=text), negative_prompt

    def generate(self, prompt: str, negative_prompt: str, output_path: Path) -> None:
        if not self._pipe:
            self._pipe = ZImagePipeline.from_pretrained(
                settings.image_model,
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
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
