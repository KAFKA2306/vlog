import threading
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.infrastructure.settings import settings


class AudioRecorder:
    def __init__(self):
        self._base_dir = Path(settings.recording_dir).expanduser().resolve()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._segments: list[str] = []
        self._lock = threading.Lock()

    def start(self) -> str:
        with self._lock:
            if self._segments:
                return self._segments[-1]
            self._base_dir.mkdir(parents=True, exist_ok=True)
            initial_path = str(
                self._base_dir / datetime.now().strftime("%Y%m%d_%H%M%S.wav")
            )
            self._segments = [initial_path]
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._record_loop, daemon=True)
            self._thread.start()
            return initial_path

    def stop(self) -> tuple[str, ...] | None:
        if not (thread := self._thread):
            return tuple(self._segments) if self._segments else None
        self._stop_event.set()
        thread.join()
        with self._lock:
            self._thread = None
            return tuple(self._segments)

    @property
    def is_recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _record_loop(self):
        start_time = datetime.now()

        while not self._stop_event.is_set():
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > 1800:
                new_path = str(
                    self._base_dir / datetime.now().strftime("%Y%m%d_%H%M%S.wav")
                )
                with self._lock:
                    self._segments.append(new_path)
                start_time = datetime.now()

            current_path = Path(self._segments[-1])
            with (
                sf.SoundFile(
                    current_path,
                    mode="w",
                    samplerate=settings.sample_rate,
                    channels=settings.channels,
                    subtype="PCM_16",
                    format="WAV",
                ) as file,
                sd.InputStream(
                    samplerate=settings.sample_rate,
                    channels=settings.channels,
                    blocksize=settings.block_size,
                ) as stream,
            ):
                while (
                    not self._stop_event.is_set()
                    and (datetime.now() - start_time).total_seconds() <= 1800
                ):
                    data, _ = stream.read(settings.block_size)
                    rms_source = (
                        np.frombuffer(data, dtype=np.int16)
                        if isinstance(data, bytes)
                        else data
                    )
                    if rms_source.size > 0:
                        rms = np.sqrt(np.mean(np.square(rms_source)))
                        if rms > settings.silence_threshold:
                            file.write(data)
