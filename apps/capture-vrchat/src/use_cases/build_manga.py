from pathlib import Path

from src.infrastructure.ai import ImageGenerator, MangaScriptGenerator
from src.infrastructure.settings import settings


def build_manga(novel_file: str) -> None:
    novel_path = Path(novel_file)
    novel_text = novel_path.read_text(encoding="utf-8")

    script = MangaScriptGenerator().generate(novel_text)

    stem = novel_path.stem
    out_dir = settings.manga_out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manga_img_path = out_dir / f"{stem}_manga.png"
    manga_md_path = out_dir / f"{stem}_manga.md"

    negative_prompt = settings.prompts["image_generator"]["negative_prompt"]
    ImageGenerator().generate(
        prompt=script["image_prompt"],
        negative_prompt=negative_prompt,
        output_path=manga_img_path,
    )

    dialogs = script.get("dialogs", [])
    md_lines = [
        f"# {stem} 漫画",
        "",
        f"![漫画](./{manga_img_path.name})",
        "",
    ]
    for i, dialog in enumerate(dialogs, 1):
        md_lines.append(f"**{i}.** {dialog}")
    md_lines.append("")

    manga_md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ Generated manga at {manga_md_path}")
