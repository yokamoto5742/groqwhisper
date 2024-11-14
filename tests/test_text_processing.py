import tempfile
import os
from unittest.mock import patch
from service_text_processing import load_replacements, replace_text, copy_and_paste_transcription


def test_load_replacements():
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as temp_file:
        temp_file.write("old,new\ntest,テスト")

    temp_file_path = temp_file.name

    with patch('service_text_processing.get_replacements_path', return_value=temp_file_path):
        replacements = load_replacements()

    assert replacements == {"old": "new", "test": "テスト"}

    os.unlink(temp_file_path)


def test_replace_text():
    replacements = {"old": "new", "test": "テスト"}
    text = "This is an old test."
    result = replace_text(text, replacements)
    assert result == "This is an new テスト."


@patch('pyperclip.copy')
@patch('threading.Timer')
def test_copy_and_paste_transcription(mock_timer, mock_copy):
    text = "テストテキスト"
    replacements = {"テスト": "test"}
    config = {'CLIPBOARD': {'PASTE_DELAY': '0.5'}}

    copy_and_paste_transcription(text, replacements, config)

    mock_copy.assert_called_once_with("testテキスト")
    mock_timer.assert_called_once()
