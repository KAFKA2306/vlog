import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from src.infrastructure.settings import settings

if TYPE_CHECKING:
    from faster_whisper import WhisperModel


logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self) -> None:
        self._model: "WhisperModel" | None = None

    def _preload_cuda_libraries(self) -> None:
        """CUDA使用時にcudnn/cublasを明示ロードして依存解決を安定化。"""

        if not settings.whisper_device.startswith("cuda"):
            return

        import ctypes

        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        base = Path(sys.prefix) / "lib" / pyver / "site-packages" / "nvidia"
        roots = [base / "cudnn" / "lib", base / "cublas" / "lib"]
        for root in roots:
            if not root.is_dir():
                continue
            for lib in root.iterdir():
                if lib.suffix not in {".so", ".so.9", ".so.12"}:
                    continue
                try:
                    ctypes.CDLL(str(lib), mode=ctypes.RTLD_GLOBAL)
                    logger.debug("CUDAライブラリをプリロード: %s", lib)
                except OSError as exc:
                    logger.warning("CUDAライブラリをロードできませんでした: %s (%s)", lib, exc)

    def _cuda_libraries_present(self) -> bool:
        import ctypes

        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        base = Path(sys.prefix) / "lib" / pyver / "site-packages" / "nvidia"
        candidates = [
            base / "cudnn" / "lib" / "libcudnn_ops.so.9",
            base / "cublas" / "lib" / "libcublas.so.12",
        ]
        loaded_any = False
        for lib_path in candidates:
            try:
                ctypes.CDLL(str(lib_path))
                loaded_any = True
            except OSError as exc:
                logger.warning("CUDAライブラリ未検出: %s (%s)", lib_path, exc)
                return False
        return loaded_any

    def _candidate_configs(self) -> list[tuple[str, str, str]]:
        device = settings.whisper_device
        force_cuda = os.getenv("VLOG_ALLOW_UNSAFE_CUDA", "0").lower() in {
            "1",
            "true",
            "yes",
        }

        if device.startswith("cuda") and not force_cuda:
            logger.info("デフォルトで安全策としてCPUに切替（VLOG_ALLOW_UNSAFE_CUDA=1で強制GPU）")
            device = "cpu"
        if device.startswith("cuda") and not self._cuda_libraries_present():
            logger.info("CUDAライブラリ不足のためCPUへフォールバック")
            device = "cpu"

        compute = settings.whisper_compute_type
        if device == "cpu" and compute not in {"int8", "int8_float16", "int16"}:
            compute = "int8"

        primary = (settings.whisper_model_size, device, compute)
        fallbacks: list[tuple[str, str, str]] = [primary]
        if device != "cpu":
            fallbacks.append((settings.whisper_model_size, "cpu", "int8"))
        if settings.whisper_model_size != "base":
            fallbacks.append(("base", "cpu", "int8"))

        uniq: list[tuple[str, str, str]] = []
        for cfg in fallbacks:
            if cfg not in uniq:
                uniq.append(cfg)
        return uniq

    @property
    def model(self) -> "WhisperModel":
        if self._model is None:
            self._preload_cuda_libraries()
            from faster_whisper import WhisperModel

            errors: list[str] = []
            for model_size, device, compute_type in self._candidate_configs():
                try:
                    logger.info(
                        "Whisperモデルをロード: size=%s device=%s compute=%s",
                        model_size,
                        device,
                        compute_type,
                    )
                    self._model = WhisperModel(
                        model_size,
                        device=device,
                        compute_type=compute_type,
                    )
                    break
                except Exception as exc:
                    msg = (
                        f"size={model_size} device={device} compute={compute_type}: {exc}"
                    )
                    logger.warning("Whisperロード失敗: %s", msg)
                    errors.append(msg)

            if self._model is None:
                raise RuntimeError(
                    "Whisperモデルを全候補でロードできませんでした: "
                    + " | ".join(errors)
                )
        return self._model

    def transcribe(self, audio_path: str) -> str:
        try:
            segments, _ = self.model.transcribe(
                audio_path,
                beam_size=settings.whisper_beam_size,
                vad_filter=settings.whisper_vad_filter,
            )
            collected = [segment.text.strip() for segment in segments]
            transcript = " ".join(text for text in collected if text)
            if transcript.strip():
                return transcript.strip()
            return "（無音または音声が検出できませんでした）"
        except Exception as exc:
            logger.error("文字起こしに失敗しました", exc_info=exc)
            return "（文字起こしに失敗しました。このログを確認してください）"

    def _save_transcript(self, audio_path: str, text: str) -> str:
        os.makedirs(settings.transcript_dir, exist_ok=True)
        base = Path(audio_path).stem
        out_path = Path(settings.transcript_dir) / f"{base}.txt"
        out_path.write_text(text + "\n", encoding="utf-8")
        logger.info("Transcriptを保存: %s", out_path)
        return str(out_path)

    def transcribe_and_save(self, audio_path: str) -> tuple[str, str]:
        text = self.transcribe(audio_path)
        path = self._save_transcript(audio_path, text)
        return text, path

    def unload(self) -> None:
        self._model = None
