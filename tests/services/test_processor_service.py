from datetime import datetime
from unittest.mock import MagicMock

from src.domain.entities import RecordingSession
from src.services.processor_service import ProcessorService


def test_process_session():
    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = "transcript"
    
    mock_summarizer = MagicMock()
    mock_summarizer.summarize.return_value = "summary"
    
    mock_writer = MagicMock()
    mock_writer.write.return_value = "/path/to/diary.md"
    
    service = ProcessorService(mock_transcriber, mock_summarizer, mock_writer)
    
    session = RecordingSession(
        start_time=datetime.now(),
        file_path="/path/to/audio.wav",
        end_time=datetime.now()
    )
    
    entry = service.process_session(session)
    
    assert entry.summary == "summary"
    assert entry.raw_log == "transcript"
    assert entry.diary_path == "/path/to/diary.md"
    
    mock_transcriber.transcribe.assert_called_with("/path/to/audio.wav")
    mock_summarizer.summarize.assert_called_with("transcript", session)
    mock_writer.write.assert_called_once()
