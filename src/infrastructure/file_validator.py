import wave
from pathlib import Path

from src.infrastructure.settings import settings


class FileValidator:
    def is_valid_for_processing(self, audio_path: str) -> tuple[bool, str | None]:
        file_path = Path(audio_path)

        if not file_path.exists():
            return False, f"ファイルが存在しません: {audio_path}"

        file_size = file_path.stat().st_size
        if file_size < settings.min_file_size_bytes:
            size_kb = file_size / 1024
            min_kb = settings.min_file_size_bytes / 1024
            return (
                False,
                f"ファイルサイズが小さすぎます: {size_kb:.1f}KB < {min_kb:.1f}KB",
            )

        duration = self._get_audio_duration(audio_path)
        if duration < settings.min_duration_seconds:
            return (
                False,
                f"音声が短すぎます: {duration:.1f}秒 < "
                f"{settings.min_duration_seconds}秒",
            )

        if settings.skip_if_processed:
            base_name = file_path.stem
            transcript_exists = (
                Path(settings.transcript_dir) / f"{base_name}.txt"
            ).exists()
            cleaned_transcript_exists = (
                Path(settings.transcript_dir) / f"cleaned_{base_name}.txt"
            ).exists()

            if transcript_exists and cleaned_transcript_exists:
                return False, "処理済み（トランスクリプト存在）"

        return True, None

    def _get_audio_duration(self, audio_path: str) -> float:
        file_path = Path(audio_path)

        if file_path.suffix.lower() == ".wav":
            with wave.open(str(file_path), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return frames / float(rate)

        if file_path.suffix.lower() in {".flac", ".mp3", ".m4a"}:
            import soundfile as sf

            info = sf.info(str(file_path))
            return info.duration

        from pydub import AudioSegment

        audio = AudioSegment.from_file(str(file_path))
        return len(audio) / 1000.0
