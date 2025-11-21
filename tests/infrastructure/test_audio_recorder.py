from unittest.mock import patch

from src.infrastructure.audio_recorder import AudioRecorder


def test_start_creates_file_and_thread():
    recorder = AudioRecorder()
    with patch("src.infrastructure.audio_recorder.sd.InputStream") as MockStream, \
         patch("src.infrastructure.audio_recorder.sf.SoundFile"), \
         patch("os.makedirs"):
        
        # Configure stream.read to return a tuple (data, overflow)
        mock_stream_instance = MockStream.return_value
        mock_stream_instance.__enter__.return_value = mock_stream_instance
        mock_stream_instance.read.return_value = (b'\x00' * 1024, False)
        
        path = recorder.start()
        
        assert path.endswith(".flac")
        assert recorder.is_recording
        
        # Start again should return same path
        path2 = recorder.start()
        assert path == path2

def test_stop_stops_thread():
    recorder = AudioRecorder()
    with patch("src.infrastructure.audio_recorder.sd.InputStream") as MockStream, \
         patch("src.infrastructure.audio_recorder.sf.SoundFile"), \
         patch("os.makedirs"):
        
        # Configure stream.read to return a tuple (data, overflow)
        mock_stream_instance = MockStream.return_value
        mock_stream_instance.__enter__.return_value = mock_stream_instance
        mock_stream_instance.read.return_value = (b'\x00' * 1024, False)
        
        recorder.start()
        assert recorder.is_recording
        
        path = recorder.stop()
        assert not recorder.is_recording
        assert path.endswith(".flac")
