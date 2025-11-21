import os
import sys
from pathlib import Path

from faster_whisper import WhisperModel

from src.infrastructure.settings import settings


class Transcriber:
    def __init__(self) -> None:
        self._model: WhisperModel | None = None

    def _append_cuda_library_path(self) -> None:
        if not settings.whisper_device.startswith("cuda"):
            return
        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        base = Path(sys.prefix) / "lib" / pyver / "site-packages" / "nvidia"
        candidates = [base / "cudnn" / "lib", base / "cublas" / "lib"]
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        to_add: list[str] = []
        for path in candidates:
            if path.is_dir():
                path_str = str(path)
                if path_str not in existing:
                    to_add.append(path_str)
        if to_add:
            os.environ["LD_LIBRARY_PATH"] = ":".join(
                to_add + ([existing] if existing else [])
            )

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            self._append_cuda_library_path()
            self._model = WhisperModel(
                settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
        return self._model

    def transcribe(self, audio_path: str) -> str:
        segments, _ = self.model.transcribe(
            audio_path,
            beam_size=settings.whisper_beam_size,
            vad_filter=settings.whisper_vad_filter,
        )
        collected = [segment.text.strip() for segment in segments]
        return " ".join(text for text in collected if text)

    def unload(self) -> None:
        self._model = None
