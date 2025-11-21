from faster_whisper import WhisperModel

from src.infrastructure.settings import settings


class Transcriber:
    def __init__(self) -> None:
        self._model: WhisperModel | None = None

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
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
        transcript = " ".join(segment.text.strip() for segment in segments)
        return transcript.strip()

    def unload(self) -> None:
        self._model = None
