import os
import threading
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.infrastructure.settings import settings


class AudioRecorder:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._file_path: str | None = None
        self._lock = threading.Lock()

    def start(self) -> str:
        with self._lock:
            if self.is_recording and self._file_path:
                return self._file_path
            if self.is_recording:
                return ""
            os.makedirs(settings.recording_dir, exist_ok=True)
            filename = datetime.now().strftime("%Y%m%d_%H%M%S.flac")
            self._file_path = os.path.join(settings.recording_dir, filename)
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._record_loop,
                args=(self._file_path,),
                daemon=True,
            )
            self._thread.start()
            return self._file_path

    def stop(self) -> str | None:
        thread: threading.Thread | None
        with self._lock:
            thread = self._thread
            if not thread:
                return self._file_path
            self._stop_event.set()
        thread.join()
        with self._lock:
            self._thread = None
            return self._file_path

    @property
    def is_recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _record_loop(self, initial_file_path: str):
        current_file_path = initial_file_path
        start_time = datetime.now()

        while not self._stop_event.is_set():
            if (datetime.now() - start_time).total_seconds() > 1800:
                filename = datetime.now().strftime("%Y%m%d_%H%M%S.flac")
                current_file_path = os.path.join(settings.recording_dir, filename)
                start_time = datetime.now()
                with self._lock:
                    self._file_path = current_file_path

            with sf.SoundFile(
                current_file_path,
                mode="w",
                samplerate=settings.sample_rate,
                channels=settings.channels,
                subtype="PCM_16",
                format="FLAC",
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
