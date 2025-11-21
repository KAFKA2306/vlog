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
        self._file_path: str | None = None
        self._segments: list[str] = []
        self._lock = threading.Lock()

    def start(self) -> str:
        with self._lock:
            if self.is_recording and self._file_path:
                return self._file_path
            if self.is_recording:
                return ""
            self._base_dir.mkdir(parents=True, exist_ok=True)
            filename = datetime.now().strftime("%Y%m%d_%H%M%S.wav")
            self._file_path = str(self._base_dir / filename)
            self._segments = [self._file_path]
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._record_loop,
                args=(self._file_path,),
                daemon=True,
            )
            self._thread.start()
            return self._file_path

    def stop(self) -> tuple[str, ...] | None:
        thread: threading.Thread | None
        with self._lock:
            thread = self._thread
            if not thread:
                return tuple(self._segments) if self._segments else None
            self._stop_event.set()
        thread.join()
        with self._lock:
            self._thread = None
            return tuple(self._segments)

    @property
    def is_recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _record_loop(self, initial_file_path: str):
        current_file_path = Path(initial_file_path)
        start_time = datetime.now()

        while not self._stop_event.is_set():
            if (datetime.now() - start_time).total_seconds() > 1800:
                filename = datetime.now().strftime("%Y%m%d_%H%M%S.wav")
                current_file_path = self._base_dir / filename
                start_time = datetime.now()
                with self._lock:
                    self._file_path = str(current_file_path)
                    self._segments.append(self._file_path)

            with sf.SoundFile(
                current_file_path,
                mode="w",
                samplerate=settings.sample_rate,
                channels=settings.channels,
                subtype="PCM_16",
                format="WAV",
            ) as file:
                with sd.InputStream(
                    samplerate=settings.sample_rate,
                    channels=settings.channels,
                    blocksize=settings.block_size,
                ) as stream:
                    while not self._stop_event.is_set():
                        if (datetime.now() - start_time).total_seconds() > 1800:
                            break
                        data, _ = stream.read(settings.block_size)
                        if isinstance(data, bytes):
                            rms_source = np.frombuffer(data, dtype=np.int16)
                        else:
                            rms_source = data
                        if rms_source.size == 0:
                            continue
                        rms = np.sqrt(np.mean(np.square(rms_source)))
                        if rms > settings.silence_threshold:
                            file.write(data)
