from unittest.mock import Mock, patch
import tempfile
import os
from service_transcription import transcribe_audio


@patch('groq.Groq')
def test_transcribe_audio(mock_groq):
    mock_client = Mock()
    mock_groq.return_value = mock_client
    mock_client.audio.transcriptions.create.return_value = "これはテストです。"

    config = {
        'WHISPER': {
            'MODEL': 'whisper-1',
            'PROMPT': '',
            'LANGUAGE': 'ja'
        }
    }

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_file.write(b'\x00' * 1024)  # ダミーのオーディオデータ

    result = transcribe_audio(temp_file.name, True, True, config, mock_client)
    assert result == "これはテストです。"

    result_no_punctuation = transcribe_audio(temp_file.name, False, True, config, mock_client)
    assert result_no_punctuation == "これはテストです"

    os.unlink(temp_file.name)
