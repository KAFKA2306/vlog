from faster_whisper import WhisperModel
from src.infrastructure.settings import settings

class Transcriber:
    def transcribe(self, audio_path: str) -> str:
        model = WhisperModel(settings.whisper_model_size, device=settings.whisper_device, compute_type=settings.whisper_compute_type)
        segments, _ = model.transcribe(audio_path, beam_size=5)
        return " ".join([segment.text for segment in segments])
