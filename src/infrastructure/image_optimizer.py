import io
from pathlib import Path
from typing import Tuple

from PIL import Image


class ImageOptimizer:
    @staticmethod
    def to_webp(image_path: Path, quality: int = 80) -> Tuple[bytes, str]:
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            output = io.BytesIO()
            img.save(output, format="WEBP", quality=quality, method=6)
            return output.getvalue(), ".webp"
