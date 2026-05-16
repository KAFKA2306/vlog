import io
import logging
from pathlib import Path
from typing import Tuple

try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """画像の最適化を行うクラス"""

    @staticmethod
    def to_webp(image_path: Path, quality: int = 80) -> Tuple[bytes, str]:
        """
        指定された画像をWebP形式に変換し、バイナリと拡張子を返す。
        Pillowが利用できない場合や変換に失敗した場合はオリジナルのPNGを返す。
        """
        if not PILLOW_AVAILABLE:
            logger.warning("Pillow is not available. Falling back to original PNG.")
            return image_path.read_bytes(), ".png"

        try:
            with Image.open(image_path) as img:
                # RGBに変換（PNGのRGBAなどを考慮）
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

                output = io.BytesIO()
                img.save(output, format="WEBP", quality=quality, method=6)
                return output.getvalue(), ".webp"
        except Exception as e:
            logger.error(f"Failed to convert {image_path} to WebP: {e}")
            return image_path.read_bytes(), ".png"
