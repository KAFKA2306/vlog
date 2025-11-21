from unittest.mock import MagicMock

from src.services.recorder_service import RecorderService


def test_start_session():
    mock_recorder = MagicMock()
    mock_recorder.start.return_value = "/path/to/audio.wav"
    service = RecorderService(mock_recorder)
    
    session = service.start_session()
    
    assert session.file_path == "/path/to/audio.wav"
    assert session.start_time is not None
    assert service.active_session == session
    mock_recorder.start.assert_called_once()

def test_stop_session():
    mock_recorder = MagicMock()
    mock_recorder.start.return_value = "/path/to/audio.wav"
    mock_recorder.stop.return_value = "/path/to/audio.wav"
    service = RecorderService(mock_recorder)
    
    service.start_session()
    session = service.stop_session()
    
    assert session.end_time is not None
    assert service.active_session is None
    mock_recorder.stop.assert_called_once()
