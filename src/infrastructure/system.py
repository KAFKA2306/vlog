from __future__ import annotations

import os
import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import psutil

from src.infrastructure.settings import settings

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

SILENCE_THRESHOLD = 0.02
_RECORD_START_TIMEOUT_SECONDS = 10.0
_RECORD_STOP_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class ResourceSnapshot:
    gpu_vram_free_mib: int | None
    cpu_percent: float | None


class SystemResourceMonitor:
    def snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(
            gpu_vram_free_mib=self._gpu_vram_free_mib(),
            cpu_percent=float(psutil.cpu_percent(interval=0.1)),
        )

    def is_idle_for_heavy_work(
        self,
        *,
        min_gpu_vram_free_mib: int = 2000,
        max_cpu_percent: float = 75.0,
        snapshot: ResourceSnapshot | None = None,
    ) -> tuple[bool, str | None, ResourceSnapshot]:
        current = snapshot or self.snapshot()
        if current.gpu_vram_free_mib is None:
            return False, "GPU VRAM unavailable", current
        if current.gpu_vram_free_mib < min_gpu_vram_free_mib:
            return (
                False,
                f"Low GPU VRAM: {current.gpu_vram_free_mib}MiB free",
                current,
            )
        if current.cpu_percent is not None and current.cpu_percent > max_cpu_percent:
            return (
                False,
                f"High CPU usage: {current.cpu_percent:.1f}% busy",
                current,
            )
        return True, None, current

    def _gpu_vram_free_mib(self) -> int | None:
        try:
            output = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.free",
                    "--format=csv,noheader,nounits",
                ],
                encoding="utf-8",
            )
        except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
            return None
        values = [int(line.strip()) for line in output.splitlines() if line.strip()]
        return min(values) if values else None


class RecordingThreadError(RuntimeError):
    pass


class AudioRecorder:
    def __init__(self) -> None:
        self._base_dir = settings.recording_dir
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._started_event = threading.Event()
        self._current_file: str | None = None
        self._last_error: Exception | None = None
        self._lock = threading.Lock()

    def start(self) -> str:
        with self._lock:
            if self._current_file and self.is_recording:
                return self._current_file
            os.makedirs(self._base_dir, exist_ok=True)
            self._current_file = os.path.join(
                self._base_dir, datetime.now().strftime("%Y%m%d_%H%M%S.flac")
            )
            self._last_error = None
            self._stop_event.clear()
            self._started_event.clear()
            self._thread = threading.Thread(
                target=self._record_loop,
                name="vlog-audio-recorder",
                daemon=True,
            )
            self._thread.start()

        if not self._started_event.wait(_RECORD_START_TIMEOUT_SECONDS):
            self._stop_event.set()
            thread = self._thread
            if thread is not None:
                thread.join(timeout=1.0)
            self._cleanup_state(remove_empty=True)
            raise TimeoutError("Audio input stream did not open within 10 seconds")
        if self._last_error is not None:
            error = self._last_error
            self._cleanup_state(remove_empty=True)
            raise RecordingThreadError("Audio input stream failed to open") from error
        if not self.is_recording or self._current_file is None:
            self._cleanup_state(remove_empty=True)
            raise RecordingThreadError("Audio recording thread exited during startup")
        return self._current_file

    def stop(self) -> tuple[str, ...] | None:
        thread = self._thread
        if thread is None:
            return None
        self._stop_event.set()
        thread.join(timeout=_RECORD_STOP_TIMEOUT_SECONDS)
        if thread.is_alive():
            raise TimeoutError("Audio recording thread did not stop within 30 seconds")

        error = self._last_error
        path = self._cleanup_state(remove_empty=False)
        if error is not None:
            raise RecordingThreadError("Audio recording thread failed") from error
        if path and os.path.exists(path):
            if os.path.getsize(path) > 100:
                return (path,)
            os.unlink(path)
        return None

    @property
    def is_recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    def _cleanup_state(self, *, remove_empty: bool) -> str | None:
        with self._lock:
            path = self._current_file
            self._thread = None
            self._current_file = None
            if remove_empty and path and os.path.exists(path):
                try:
                    if os.path.getsize(path) <= 100:
                        os.unlink(path)
                except OSError:
                    pass
            return path

    def _record_loop(self) -> None:
        # PortAudio and NumPy are only required when recording actually starts.
        import numpy as np
        import sounddevice as sd
        import soundfile as sf

        try:
            path = self._current_file
            if path is None:
                raise RecordingThreadError("Recording path was not initialized")
            with (
                sf.SoundFile(
                    path,
                    mode="w",
                    samplerate=settings.sample_rate,
                    channels=settings.channels,
                    subtype="PCM_16",
                    format="FLAC",
                ) as file,
                sd.InputStream(
                    samplerate=settings.sample_rate,
                    channels=settings.channels,
                    blocksize=settings.block_size,
                ) as stream,
            ):
                self._started_event.set()
                while not self._stop_event.is_set():
                    data, overflowed = stream.read(settings.block_size)
                    if overflowed:
                        raise RecordingThreadError("Audio input overflow detected")
                    rms_source = (
                        np.frombuffer(data, dtype=np.int16)
                        if isinstance(data, bytes)
                        else data
                    )
                    if rms_source.size > 0:
                        rms = float(np.sqrt(np.mean(np.square(rms_source))))
                        if rms > SILENCE_THRESHOLD:
                            file.write(data)
        except Exception as exc:
            self._last_error = exc
            self._started_event.set()
        finally:
            self._started_event.set()


class Transcriber:
    def __init__(self) -> None:
        self._model: "WhisperModel | None" = None

    @property
    def model(self) -> "WhisperModel":
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
        return self._model

    def transcribe(self, audio_path: str) -> str:
        segments, _ = self.model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=100, speech_pad_ms=30),
        )
        return " ".join(segment.text.strip() for segment in segments).strip()

    def transcribe_and_save(self, audio_path: str) -> tuple[str, str]:
        base = Path(audio_path).stem
        os.makedirs(settings.transcript_dir, exist_ok=True)
        out_path = Path(settings.transcript_dir) / f"{base}.txt"
        if out_path.exists():
            return out_path.read_text(encoding="utf-8").strip(), str(out_path)
        text = self.transcribe(audio_path)
        out_path.write_text(text + "\n", encoding="utf-8")
        return text, str(out_path)

    def unload(self) -> None:
        self._model = None


class ProcessMonitor:
    def __init__(self) -> None:
        self._targets = {name.lower() for name in settings.process_names}
        self._last_status = False

    def is_running(self) -> bool:
        current_status = self._check_processes()
        self._last_status = current_status
        return current_status

    def _check_processes(self) -> bool:
        for proc in psutil.process_iter(["name", "exe"]):
            name = (proc.info.get("name") or "").lower()
            exe = (proc.info.get("exe") or "").lower()
            if name in self._targets or exe in self._targets:
                return True
            if any(target in name for target in self._targets):
                return True
            if any(target in exe for target in self._targets):
                return True
        return False


class TranscriptPreprocessor:
    FILLERS = [
        r"えー",
        r"あのー",
        r"うーん",
        r"えっと",
        r"なんて",
        r"まあ",
        r"そうですね",
        r"あー",
        r"んー",
        r"うん",
        r"ふん",
        r"あ",
        r"はは",
        r"ははは",
        r"なんか",
        r"え",
        r"お",
        r"ふんふん",
        r"ふんふんふん",
        r"うんうん",
        r"うんうんうん",
        r"はいはい",
        r"はいはいはい",
        r"はいはいはいはい",
        r"おー",
        r"ああ",
        r"んふん",
        r"そっか",
        r"そっかぁ",
        r"そうか",
        r"そうなんだ",
        r"えへへ",
        r"あの",
        r"あのね",
        r"あのさ",
        r"ん",
    ]

    def process(self, text: str) -> str:
        text = self._normalize_text(text)
        text = self._remove_repetition(text)
        text = self._remove_fillers(text)
        text = self._dedupe_words(text)
        return self._merge_lines(text)

    def _normalize_text(self, txt: str) -> str:
        txt = txt.replace("…", " ")
        return re.sub(r"\.{2,}", " ", txt)

    def _remove_repetition(self, txt: str) -> str:
        return re.sub(r"(.{1,4}?)\1{4,}", r"\1", txt)

    def _remove_fillers(self, txt: str) -> str:
        fillers = sorted(self.FILLERS, key=len, reverse=True)
        pattern = f"(^|[\\s、。?!])({'|'.join(fillers)})(?=[\\s、。?!]|$)"

        def repl(match: re.Match[str]) -> str:
            leading = match.group(1)
            return (leading if leading != "^" else "") + " "

        for _ in range(20):
            previous = txt
            txt = re.sub(pattern, repl, txt)
            if txt == previous:
                break
        txt = re.sub(r"\s+", " ", txt).strip()
        txt = re.sub(r"([、。])\1+", r"\1", txt)
        txt = re.sub(r"^[、。]+", "", txt).strip()
        txt = re.sub(r"\s+[、。]+", "", txt)
        return re.sub(r"\s+", " ", txt).strip()

    def _dedupe_words(self, txt: str) -> str:
        return re.sub(r"(\S+)\s+\1\b", r"\1", txt)

    def _merge_lines(self, txt: str) -> str:
        return re.sub(r"\s+", " ", txt.replace("\n", " ")).strip()
