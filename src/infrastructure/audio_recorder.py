import sounddevice as sd
import soundfile as sf
import os
from datetime import datetime
from src.infrastructure.settings import settings

class AudioRecorder:
    def __init__(self):
        self.running = False

    def start(self) -> str:
        self.running = True
        os.makedirs(settings.recording_dir, exist_ok=True)
        filename = datetime.now().strftime("%Y%m%d_%H%M%S.wav")
        filepath = os.path.join(settings.recording_dir, filename)
        
        with sf.SoundFile(filepath, mode='w', samplerate=settings.sample_rate, channels=settings.channels) as file:
            with sd.InputStream(samplerate=settings.sample_rate, channels=settings.channels, blocksize=settings.block_size) as stream:
                while self.running:
                    data, _ = stream.read(settings.block_size)
                    file.write(data)
        return filepath

    def stop(self):
        self.running = False
