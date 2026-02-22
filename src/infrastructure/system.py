import logging
import os
import re
import threading
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import psutil
import sounddevice as sd
import soundfile as sf
from typing_extensions import TYPE_CHECKING

from src.infrastructure.settings import settings

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

SILENCE_THRESHOLD = 0.02


def list_audio_devices() -> str:
    devices = sd.query_devices()
    return str(devices)


def apply_design_system():
    plt.rcParams.update(
        {
            "axes.facecolor": "#0A0A12",
            "figure.facecolor": "#0A0A12",
            "axes.edgecolor": "#00A3AF",
            "text.color": "#FFFFFF",
            "axes.labelcolor": "#FFFFFF",
            "xtick.color": "#FFFFFF",
            "ytick.color": "#FFFFFF",
            "grid.color": "rgba(255, 255, 255, 0.1)",
            "grid.alpha": 0.1,
            "font.family": "sans-serif",
        }
    )
    plt.rcParams["axes.prop_cycle"] = plt.cycler(
        color=["#00A3AF", "#005CB9", "#FF2A6D"]
    )


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
            self._current_file = str(
                Path(self._base_dir) / datetime.now().strftime("%Y%m%d_%H%M%S.flac")
            ).replace("\\", "/")
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
                device=settings.device_index,
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


class Transcriber:
    def __init__(self) -> None:
        self._model: "WhisperModel" | None = None

    @property
    def model(self) -> "WhisperModel":
        if self._model is None:
            import torch
            from faster_whisper import WhisperModel

            model_path = settings.whisper_model_size
            device = settings.whisper_device
            compute_type = settings.whisper_compute_type

            # Inject library path for cuDNN
            if device == "cuda":
                import sys

                base = Path(__file__).resolve().parent.parent.parent
                is_windows = sys.platform == "win32"
                venv_name = ".venv-win" if is_windows else ".venv"
                venv_lib = base / venv_name

                # Search for cuDNN libraries
                search_pattern = (
                    "nvidia/cudnn/bin" if is_windows else "nvidia/cudnn/lib"
                )
                cudnn_libs = list(venv_lib.rglob(search_pattern))

                if cudnn_libs:
                    lib_path = str(cudnn_libs[0])
                    if is_windows:
                        # Windows: add_dll_directory is preferred for Python 3.8+
                        if hasattr(os, "add_dll_directory"):
                            try:
                                os.add_dll_directory(lib_path)
                                logger.info("Added DLL directory: %s", lib_path)
                            except Exception:
                                pass
                        # Also add to PATH as fallback or for older versions/tools
                        current_path = os.environ.get("PATH", "")
                        if lib_path not in current_path:
                            os.environ["PATH"] = f"{lib_path};{current_path}"
                            logger.info("Injected PATH for CUDA: %s", lib_path)
                    else:
                        # Linux: LD_LIBRARY_PATH
                        current_ld = os.environ.get("LD_LIBRARY_PATH", "")
                        if lib_path not in current_ld:
                            new_ld = f"{lib_path}:{current_ld}".strip(":")
                            os.environ["LD_LIBRARY_PATH"] = new_ld
                            logger.info("Injected LD_LIBRARY_PATH: %s", lib_path)

            if device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA not available. Falling back to CPU.")
                device = "cpu"
                compute_type = "int8"

            try:
                if device == "cuda":
                    # Simple check if libs are loadable
                    self._model = WhisperModel(
                        model_path,
                        device=device,
                        compute_type=compute_type,
                    )
                else:
                    raise ValueError("Force CPU")
            except Exception as e:
                if device == "cuda":
                    logger.warning(
                        "CUDA initialization failed: %s. Falling back to CPU.", e
                    )
                device = "cpu"
                compute_type = "int8"
                self._model = WhisperModel(
                    model_path,
                    device=device,
                    compute_type=compute_type,
                )
        return self._model

    def transcribe(self, audio_path: str) -> str:
        segments = self.transcribe_segments(audio_path)
        return " ".join(segment.text.strip() for segment in segments).strip()

    def transcribe_segments(self, audio_path: str) -> list:
        segments, _ = self.model.transcribe(
            audio_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=100, speech_pad_ms=30),
            word_timestamps=True,
        )
        return list(segments)

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


class Diarizer:
    def __init__(self):
        self._pipeline = None

    @property
    def pipeline(self):
        if self._pipeline is None:
            import torch
            from pyannote.audio import Pipeline

            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=settings.huggingface_token,
            )
            if self._pipeline is not None and torch.cuda.is_available():
                self._pipeline.to(torch.device("cuda"))
        return self._pipeline

    def diarize(self, audio_path: str) -> list[tuple[float, float, str]]:
        pipeline = self.pipeline
        diarization = pipeline(audio_path)
        results = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            results.append((turn.start, turn.end, speaker))
        return results


class ProcessMonitor:
    def __init__(self):
        self._targets = {name.lower() for name in settings.process_names}
        self._last_status = False
        self._logged_sample = False

    def is_running(self) -> bool:
        current_status = self._check_processes()
        if current_status != self._last_status:
            self._last_status = current_status
            if current_status:
                logger.info("Target process detected.")
                self._logged_sample = False
            else:
                logger.info("Target process no longer detected.")
        if not current_status and not self._logged_sample:
            sample = self._sample_processes()
            logger.info("No target found. Sample running processes: %s", sample)
            self._logged_sample = True
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

    def _sample_processes(self) -> list[str]:
        names = []
        for proc in psutil.process_iter(["name"]):
            if len(names) >= 10:
                break
            name = proc.info.get("name")
            if name:
                names.append(name)
        return names


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
        r"うんうん埋ん",
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
        txt = self._normalize_text(text)
        txt = self._remove_repetition(txt)
        txt = self._remove_fillers(txt)
        txt = self._dedupe_words(txt)
        txt = self._merge_lines(txt)
        return txt

    def _normalize_text(self, txt: str) -> str:
        txt = txt.replace("…", " ")
        txt = re.sub(r"\.{2,}", " ", txt)
        return txt

    def _remove_repetition(self, txt: str) -> str:
        return re.sub(r"(.{1,4}?)\1{4,}", r"\1", txt)

    def _remove_fillers(self, txt: str) -> str:
        fillers = sorted(self.FILLERS, key=len, reverse=True)
        pattern_str = "|".join(str(f) for f in fillers)
        pattern = f"(^|[\\s、。?!])({pattern_str})(?=[\\s、。?!]|$)"

        def repl(match: re.Match[str]) -> str:
            leading = match.group(1)
            return (leading if leading != "^" else "") + " "

        for _ in range(20):
            prev_txt = txt
            txt = re.sub(pattern, repl, txt)
            if txt == prev_txt:
                break

        txt = re.sub(r"\s+", " ", txt).strip()
        txt = re.sub(r"([、。])\1+", r"\1", txt)
        txt = re.sub(r"^[、。]+", "", txt).strip()
        txt = re.sub(r"\s+[、。]+", "", txt)
        return re.sub(r"\s+", " ", txt).strip()

    def _dedupe_words(self, txt: str) -> str:
        return re.sub(r"(\S+)\s+\1\b", r"\1", txt)

    def _merge_lines(self, txt: str) -> str:
        txt = txt.replace("\n", " ")
        return re.sub(r"\s+", " ", txt).strip()
