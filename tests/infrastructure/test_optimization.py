from unittest.mock import patch

import numpy as np

from src.infrastructure.audio_recorder import AudioRecorder
from src.infrastructure.settings import settings
from src.infrastructure.transcriber import Transcriber


def test_silence_cutting():
    recorder = AudioRecorder()
    with (
        patch("src.infrastructure.audio_recorder.sd.InputStream") as MockStream,
        patch("src.infrastructure.audio_recorder.sf.SoundFile") as MockFile,
        patch("os.makedirs"),
    ):
        # Mock file instance
        mock_file_instance = MockFile.return_value
        mock_file_instance.__enter__.return_value = mock_file_instance

        # Mock stream instance
        mock_stream_instance = MockStream.return_value
        mock_stream_instance.__enter__.return_value = mock_stream_instance

        # Create dummy data
        silent_data = np.zeros(settings.block_size, dtype=np.float32)
        loud_data = np.ones(settings.block_size, dtype=np.float32)

        # Configure stream.read to return silent then loud data
        # We need to control the loop, so we'll let it run twice then stop
        mock_stream_instance.read.side_effect = [
            (silent_data, False),
            (loud_data, False),
            Exception("Stop loop"),  # Hack to stop the loop
        ]

        # _record_loopが例外で抜ける前提でロジックだけを検証する
        try:
            recorder._record_loop("dummy.wav")
        except Exception:
            pass

        # Verify write was called only once (for loud data)
        # Note: This depends on settings.silence_threshold. Default is 0.01.
        # RMS of zeros is 0. RMS of ones is 1.

        # Check calls to file.write
        assert mock_file_instance.write.call_count == 1
        mock_file_instance.write.assert_called_with(loud_data)


def test_model_unloading(mocker):
    # Mock WhisperModel class
    mocker.patch("src.infrastructure.transcriber.WhisperModel")

    transcriber = Transcriber()

    # Access model to initialize it
    _ = transcriber.model
    assert transcriber._model is not None

    # Unload
    transcriber.unload()
    assert transcriber._model is None
