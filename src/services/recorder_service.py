import signal
import sys

from src.infrastructure.audio_recorder import AudioRecorder


def main():
    recorder = AudioRecorder()

    def signal_handler(sig, frame):
        recorder.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    recorder.start()


if __name__ == "__main__":
    main()
