import pytest
import os
from unittest.mock import Mock, patch, mock_open
from service_transcription import setup_groq_client, transcribe_audio
from groq import Groq


# テスト用の設定
@pytest.fixture
def mock_config():
    return {
        'WHISPER': {
            'MODEL': 'whisper-1',
            'PROMPT': 'テスト用プロンプト',
            'LANGUAGE': 'ja'
        }
    }


@pytest.fixture
def mock_groq_client():
    mock_client = Mock(spec=Groq)
    # audioプロパティとその下層構造をセットアップ
    mock_client.audio = Mock()
    mock_client.audio.transcriptions = Mock()
    mock_client.audio.transcriptions.create = Mock()
    return mock_client


# setup_groq_clientのテスト
def test_setup_groq_client_success():
    with patch.dict(os.environ, {'GROQ_API_KEY': 'test-api-key'}):
        client = setup_groq_client()
        assert isinstance(client, Groq)


def test_setup_groq_client_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GROQ_API_KEYの環境変数が未設定です"):
            setup_groq_client()


# transcribe_audioのテスト
def test_transcribe_audio_success(mock_groq_client, mock_config):
    # モックの設定
    mock_response = "これはテスト用の文字起こし結果です。"
    mock_groq_client.audio.transcriptions.create.return_value = mock_response

    # テストデータ
    test_audio_path = "test.wav"
    mock_file_content = b"dummy audio content"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        result = transcribe_audio(
            test_audio_path,
            use_punctuation=True,
            use_comma=True,
            config=mock_config,
            client=mock_groq_client
        )

    assert result == mock_response
    mock_groq_client.audio.transcriptions.create.assert_called_once()


def test_transcribe_audio_no_punctuation(mock_groq_client, mock_config):
    mock_response = "これは。テスト用の、文字起こし結果です。"
    mock_groq_client.audio.transcriptions.create.return_value = mock_response

    test_audio_path = "test.wav"
    with patch("builtins.open", mock_open(read_data=b"dummy audio content")):
        result = transcribe_audio(
            test_audio_path,
            use_punctuation=False,
            use_comma=True,
            config=mock_config,
            client=mock_groq_client
        )

    assert result == "これはテスト用の、文字起こし結果です"


def test_transcribe_audio_no_comma(mock_groq_client, mock_config):
    mock_response = "これは。テスト用の、文字起こし結果です。"
    mock_groq_client.audio.transcriptions.create.return_value = mock_response

    test_audio_path = "test.wav"
    with patch("builtins.open", mock_open(read_data=b"dummy audio content")):
        result = transcribe_audio(
            test_audio_path,
            use_punctuation=True,
            use_comma=False,
            config=mock_config,
            client=mock_groq_client
        )

    assert result == "これは。テスト用の文字起こし結果です。"


def test_transcribe_audio_empty_path(mock_groq_client, mock_config):
    result = transcribe_audio(
        "",
        use_punctuation=True,
        use_comma=True,
        config=mock_config,
        client=mock_groq_client
    )

    assert result is None
    mock_groq_client.audio.transcriptions.create.assert_not_called()


def test_transcribe_audio_file_error(mock_groq_client, mock_config):
    test_audio_path = "nonexistent.wav"

    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError()
        result = transcribe_audio(
            test_audio_path,
            use_punctuation=True,
            use_comma=True,
            config=mock_config,
            client=mock_groq_client
        )

    assert result is None
    mock_groq_client.audio.transcriptions.create.assert_not_called()
