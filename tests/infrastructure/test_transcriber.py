from unittest.mock import MagicMock

from src.infrastructure.transcriber import Transcriber


def test_transcribe_lazy_loads_model(mocker):
    # Mock WhisperModel class
    mock_whisper_cls = mocker.patch("src.infrastructure.transcriber.WhisperModel")
    mock_instance = mock_whisper_cls.return_value
    
    # Setup mock response
    mock_segment = MagicMock()
    mock_segment.text = "Hello world"
    mock_instance.transcribe.return_value = ([mock_segment], None)
    
    transcriber = Transcriber()
    
    # First call should initialize model
    result1 = transcriber.transcribe("dummy1.wav")
    assert result1 == "Hello world"
    
    # Second call should reuse model
    result2 = transcriber.transcribe("dummy2.wav")
    assert result2 == "Hello world"
    
    # Verify model was initialized only once
    mock_whisper_cls.assert_called_once()
    
    # Verify transcribe was called twice on the same instance
    assert mock_instance.transcribe.call_count == 2
