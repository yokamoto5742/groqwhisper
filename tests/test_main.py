import pytest
from unittest.mock import patch

@patch('tkinter.Tk')
@patch('src.gui.AudioRecorderGUI')
@patch('src.audio_recorder.AudioRecorder')
@patch('src.transcription.setup_groq_client')
@patch('src.text_processing.load_replacements')
def test_main(mock_load_replacements, mock_setup_groq_client, mock_audio_recorder, mock_gui, mock_tk):
    from src.main import main
    main()
    
    mock_tk.assert_called_once()
    mock_audio_recorder.assert_called_once()
    mock_setup_groq_client.assert_called_once()
    mock_load_replacements.assert_called_once()
    mock_gui.assert_called_once()
