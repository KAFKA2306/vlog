import logging
import os
import threading
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.infrastructure.settings import settings

SILENCE_THRESHOLD = 0.02
logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self):
        self._base_dir = settings.recording_dir
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_file: str | None = None
        self._lock = threading.Lock()

    def start(self) -> str:
        with self._lock:
            if self._current_file:
                return self._current_file

            os.makedirs(self._base_dir, exist_ok=True)
            self._current_file = os.path.join(
                self._base_dir, datetime.now().strftime("%Y%m%d_%H%M%S.flac")
            )
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._record_loop, daemon=True)
            self._thread.start()
            logger.info("Started recording to %s", self._current_file)
            return self._current_file

    def stop(self) -> tuple[str, ...] | None:
        if not self._thread:
            return None

        self._stop_event.set()
        self._thread.join()

        with self._lock:
            self._thread = None
            path = self._current_file
            self._current_file = None

            if path and os.path.exists(path):
                if os.path.getsize(path) > 100:
                    logger.info("Stopped recording. Saved %s", path)
                    return (path,)
                os.unlink(path)
                logger.info("Stopped recording. File discarded due to size: %s", path)
            return None

    @property
    def is_recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _record_loop(self):
        with (
            sf.SoundFile(
                self._current_file,
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
            while not self._stop_event.is_set():
                data, _ = stream.read(settings.block_size)
                rms_source = (
                    np.frombuffer(data, dtype=np.int16)
                    if isinstance(data, bytes)
                    else data
                )
                if rms_source.size > 0:
                    rms = np.sqrt(np.mean(np.square(rms_source)))
                    if rms > SILENCE_THRESHOLD:
                        file.write(data)
