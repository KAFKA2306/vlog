import logging
import os
import sys
from pathlib import Path

from faster_whisper import WhisperModel

from src.infrastructure.settings import settings


logger = logging.getLogger(__name__)


class Transcriber:
    def __init__(self) -> None:
        self._model: WhisperModel | None = None

    def _append_cuda_library_path(self) -> None:
        """CUDA使用時にvenv内のcudnn/cublasをLD_LIBRARY_PATHへ追加する。

        ユーザーが環境変数を手動設定し忘れても、CUDA版がロードしやすくする。
        """

        if not settings.whisper_device.startswith("cuda"):
            return

        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        base = Path(sys.prefix) / "lib" / pyver / "site-packages" / "nvidia"
        candidates = [
            base / "cudnn" / "lib",
            base / "cublas" / "lib",
        ]

        existing = os.environ.get("LD_LIBRARY_PATH", "")
        to_add: list[str] = []
        for path in candidates:
            if path.is_dir():
                path_str = str(path)
                if path_str not in existing:
                    to_add.append(path_str)

        if not to_add:
            return

        updated = ":".join(to_add + ([existing] if existing else []))
        os.environ["LD_LIBRARY_PATH"] = updated
        logger.debug("LD_LIBRARY_PATHを動的に更新: %s", updated)

    def _candidate_configs(self) -> list[tuple[str, str, str]]:
        primary = (
            settings.whisper_model_size,
            settings.whisper_device,
            settings.whisper_compute_type,
        )

        fallbacks: list[tuple[str, str, str]] = [primary]

        # CUDAが失敗した場合はCPU int8へフォールバック
        if settings.whisper_device != "cpu":
            fallbacks.append(
                (settings.whisper_model_size, "cpu", "int8")
            )

        # モデルサイズが大き過ぎる場合にbaseへ縮退
        if settings.whisper_model_size != "base":
            fallbacks.append(("base", "cpu", "int8"))

        # 重複除去
        unique: list[tuple[str, str, str]] = []
        for cfg in fallbacks:
            if cfg not in unique:
                unique.append(cfg)
        return unique

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            self._append_cuda_library_path()

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
                except Exception as exc:  # noqa: BLE001
                    message = (
                        f"size={model_size} device={device} "
                        f"compute={compute_type}: {exc}"
                    )
                    errors.append(message)
                    logger.warning("Whisperロード失敗: %s", message)

            if self._model is None:
                joined = " | ".join(errors)
                raise RuntimeError(
                    "Whisperモデルを全候補でロードできませんでした: " + joined
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
        except Exception as exc:  # noqa: BLE001
            logger.error("文字起こしに失敗しました", exc_info=exc)
            return "（文字起こしに失敗しました。このログを確認してください）"

    def unload(self) -> None:
        self._model = None
