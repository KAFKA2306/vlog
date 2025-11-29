from pathlib import Path

import google.generativeai as genai

from src.infrastructure.settings import settings


class ImageGenerator:
    def __init__(self):
        self._pipe = None
        self._model = None

    def generate_from_novel(self, chapter_text: str, output_path: Path) -> None:
        prompt, negative_prompt = self._extract_prompt(chapter_text)
        self.generate(prompt, negative_prompt, output_path)

    def _extract_prompt(self, chapter_text: str) -> tuple[str, str]:
        text = self._generate_prompt_from_novel(chapter_text)

        base_path = Path(__file__).parent

        prompt_file = base_path / "image_generator_prompt.txt"
        if prompt_file.exists():
            template = prompt_file.read_text(encoding="utf-8").strip()
        else:
            template = settings.image_generator_default_prompt

        neg_file = base_path / "image_generator_negative_prompt.txt"
        if neg_file.exists():
            negative_prompt = neg_file.read_text(encoding="utf-8").strip()
        else:
            negative_prompt = settings.image_generator_default_negative_prompt

        return template.format(text=text), negative_prompt

    def _generate_prompt_from_novel(self, chapter_text: str) -> str:
        if not self._model:
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.gemini_model)

        prompt = (
            "Analyze the following novel chapter text and generate a concise, English "
            "prompt optimized for Stable Diffusion XL (Anime Style).\n"
            "Focus on the main character's appearance, the setting, the lighting, "
            "and the mood.\n"
            "Keep it under 40 words.\n"
            "Do not include negative prompts or quality tags (like 'best quality').\n\n"
            "Novel Text:\n"
            f"{chapter_text[:2000]}\n\n"
            "Output format: Just the comma-separated keywords."
        )

        response = self._model.generate_content(prompt)
        return response.text.strip()

    def generate(self, prompt: str, negative_prompt: str, output_path: Path) -> None:
        import torch
        from diffusers import StableDiffusionXLPipeline

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
            generator=torch.Generator(settings.image_device).manual_seed(
                settings.image_seed
            ),
        ).images[0]

        image.save(output_path)
