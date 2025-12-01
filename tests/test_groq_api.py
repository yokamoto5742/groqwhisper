import logging
import os
import tempfile
from unittest.mock import Mock, mock_open, patch

import pytest

from external_service.groq_api import setup_groq_client, transcribe_audio


class TestSetupGroqClient:
    """Groqクライアント初期化のテストクラス"""

    @patch('external_service.groq_api.load_env_variables')
    @patch('external_service.groq_api.Groq')
    def test_setup_groq_client_success(self, mock_groq, mock_load_env):
        """正常系: APIキーが存在する場合のクライアント初期化"""
        # Arrange
        mock_load_env.return_value = {"GROQ_API_KEY": "test-api-key"}
        mock_client = Mock()
        mock_groq.return_value = mock_client

        # Act
        result = setup_groq_client()

        # Assert
        mock_load_env.assert_called_once()
        mock_groq.assert_called_once_with(api_key="test-api-key")
        assert result == mock_client

    @patch('external_service.groq_api.load_env_variables')
    def test_setup_groq_client_missing_api_key(self, mock_load_env):
        """異常系: APIキーが未設定の場合"""
        # Arrange
        mock_load_env.return_value = {}

        # Act & Assert
        with pytest.raises(ValueError, match="GROQ_API_KEYが未設定です"):
            setup_groq_client()

    @patch('external_service.groq_api.load_env_variables')
    def test_setup_groq_client_none_api_key(self, mock_load_env):
        """異常系: APIキーがNoneの場合"""
        # Arrange
        mock_load_env.return_value = {"GROQ_API_KEY": None}

        # Act & Assert
        with pytest.raises(ValueError, match="GROQ_API_KEYが未設定です"):
            setup_groq_client()

    @patch('external_service.groq_api.load_env_variables')
    def test_setup_groq_client_empty_api_key(self, mock_load_env):
        """異常系: APIキーが空文字の場合"""
        # Arrange
        mock_load_env.return_value = {"GROQ_API_KEY": ""}

        # Act & Assert
        with pytest.raises(ValueError, match="GROQ_API_KEYが未設定です"):
            setup_groq_client()


class TestTranscribeAudio:
    """音声文字起こし機能のテストクラス"""

    @pytest.fixture
    def mock_config(self):
        """テスト用設定データ"""
        return {
            'WHISPER': {
                'MODEL': 'whisper-large-v3',
                'PROMPT': 'テスト用プロンプト',
                'LANGUAGE': 'ja'
            }
        }

    @pytest.fixture
    def mock_client(self):
        """モックGroqクライアント"""
        client = Mock()
        transcription = Mock()
        transcription.text = "テスト文字起こし結果"
        client.audio.transcriptions.create.return_value = transcription
        return client

    @pytest.fixture
    def temp_audio_file(self):
        """一時的な音声ファイル"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio data")
            temp_path = f.name
        yield temp_path
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    def test_transcribe_audio_success(self, mock_config, mock_client, temp_audio_file):
        """正常系: 文字起こし成功"""
        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result == "テスト文字起こし結果"
        mock_client.audio.transcriptions.create.assert_called_once()

        # API呼び出しパラメータの確認
        call_args = mock_client.audio.transcriptions.create.call_args
        assert call_args[1]['model'] == 'whisper-large-v3'
        assert call_args[1]['prompt'] == 'テスト用プロンプト'
        assert call_args[1]['response_format'] == "text"
        assert call_args[1]['language'] == 'ja'

    def test_transcribe_audio_success_with_punctuation(self, mock_config, mock_client, temp_audio_file):
        """正常系: 句読点を含む文字起こし成功"""
        # Arrange
        transcription = Mock()
        transcription.text = "テスト。文字、起こし。結果"
        mock_client.audio.transcriptions.create.return_value = transcription

        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result == "テスト。文字、起こし。結果"  # 句読点はそのまま
        assert "。" in result
        assert "、" in result

    def test_transcribe_audio_success_string_response(self, mock_config, mock_client, temp_audio_file):
        """正常系: 文字列レスポンスの場合"""
        # Arrange
        mock_client.audio.transcriptions.create.return_value = "直接文字列レスポンス"

        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result == "直接文字列レスポンス"

    def test_transcribe_audio_missing_file_path(self, mock_config, mock_client):
        """異常系: ファイルパスが未指定"""
        # Act
        result = transcribe_audio("", mock_config, mock_client)

        # Assert
        assert result is None

    def test_transcribe_audio_none_file_path(self, mock_config, mock_client):
        """異常系: ファイルパスがNone"""
        # Act
        result = transcribe_audio(None, mock_config, mock_client)

        # Assert
        assert result is None

    def test_transcribe_audio_file_not_exists(self, mock_config, mock_client):
        """異常系: ファイルが存在しない"""
        # Act
        result = transcribe_audio("/non/existent/file.wav", mock_config, mock_client)

        # Assert
        assert result is None

    def test_transcribe_audio_empty_file(self, mock_config, mock_client):
        """異常系: 空ファイル"""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name  # 空ファイル

        try:
            # Act
            result = transcribe_audio(temp_path, mock_config, mock_client)

            # Assert
            assert result is None
        finally:
            os.unlink(temp_path)

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_transcribe_audio_permission_error(self, mock_open_func, mock_config, mock_client):
        """異常系: ファイルアクセス権限エラー"""
        # Act
        result = transcribe_audio("protected_file.wav", mock_config, mock_client)

        # Assert
        assert result is None

    @patch('builtins.open', side_effect=OSError("OS error"))
    def test_transcribe_audio_os_error(self, mock_open_func, mock_config, mock_client):
        """異常系: OS関連エラー"""
        # Act
        result = transcribe_audio("problematic_file.wav", mock_config, mock_client)

        # Assert
        assert result is None

    def test_transcribe_audio_api_none_response(self, mock_config, mock_client, temp_audio_file):
        """異常系: APIがNoneを返す"""
        # Arrange
        mock_client.audio.transcriptions.create.return_value = None

        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result is None

    def test_transcribe_audio_api_exception(self, mock_config, mock_client, temp_audio_file):
        """異常系: API呼び出し時の例外"""
        # Arrange
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")

        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result is None

    def test_transcribe_audio_empty_transcription_result(self, mock_config, mock_client, temp_audio_file):
        """境界値: 空の文字起こし結果"""
        # Arrange
        transcription = Mock()
        transcription.text = ""
        mock_client.audio.transcriptions.create.return_value = transcription

        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result == ""

    def test_transcribe_audio_whitespace_only_result(self, mock_config, mock_client, temp_audio_file):
        """境界値: 空白のみの文字起こし結果"""
        # Arrange
        transcription = Mock()
        transcription.text = "   \n\t   "
        mock_client.audio.transcriptions.create.return_value = transcription

        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result == "   \n\t   "  # 空白は保持される

    def test_transcribe_audio_with_logging_verification(self, mock_config, mock_client, temp_audio_file, caplog):
        """ログ出力の確認"""
        # Arrange
        caplog.set_level(logging.INFO)

        # Act
        result = transcribe_audio(temp_audio_file, mock_config, mock_client)

        # Assert
        assert result is not None
        assert "ファイル読み込み開始" in caplog.text
        assert "ファイル読み込み完了" in caplog.text
        assert "文字起こし完了" in caplog.text

    def test_transcribe_audio_large_file_simulation(self, mock_config, mock_client):
        """大きなファイルのシミュレーション"""
        # Arrange
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(large_content)
            temp_path = f.name

        try:
            transcription = Mock()
            transcription.text = "大きなファイルの文字起こし結果"
            mock_client.audio.transcriptions.create.return_value = transcription

            # Act
            result = transcribe_audio(temp_path, mock_config, mock_client)

            # Assert
            assert result == "大きなファイルの文字起こし結果"

            # ファイルサイズがログに記録されることを確認
            call_args = mock_client.audio.transcriptions.create.call_args
            file_tuple = call_args[1]['file']
            assert len(file_tuple[1]) == len(large_content)

        finally:
            os.unlink(temp_path)

    @patch('external_service.groq_api.os.path.exists')
    @patch('external_service.groq_api.os.path.getsize')
    def test_transcribe_audio_filesystem_mocking(self, mock_getsize, mock_exists, mock_config, mock_client):
        """ファイルシステム操作のモック化テスト"""
        # Arrange
        mock_exists.return_value = True
        mock_getsize.return_value = 1000

        with patch('builtins.open', mock_open(read_data=b"mock audio data")):
            transcription = Mock()
            transcription.text = "モックされたファイルからの結果"
            mock_client.audio.transcriptions.create.return_value = transcription

            # Act
            result = transcribe_audio("mock_file.wav", mock_config, mock_client)

            # Assert
            assert result == "モックされたファイルからの結果"
            mock_exists.assert_called_once_with("mock_file.wav")
            mock_getsize.assert_called_once_with("mock_file.wav")


class TestIntegrationScenarios:
    """統合シナリオテスト"""

    def test_full_workflow_success(self):
        """正常系: セットアップから文字起こしまでの完全なワークフロー"""
        # Arrange
        with patch('external_service.groq_api.load_env_variables') as mock_load_env:
            mock_load_env.return_value = {"GROQ_API_KEY": "test-key"}

            with patch('external_service.groq_api.Groq') as mock_groq_class:
                mock_client = Mock()
                mock_groq_class.return_value = mock_client

                transcription = Mock()
                transcription.text = "統合テスト成功"
                mock_client.audio.transcriptions.create.return_value = transcription

                config = {
                    'WHISPER': {
                        'MODEL': 'whisper-large-v3',
                        'PROMPT': 'テスト',
                        'LANGUAGE': 'ja'
                    }
                }

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(b"test audio")
                    temp_path = f.name

                try:
                    # Act
                    client = setup_groq_client()
                    result = transcribe_audio(temp_path, config, client)

                    # Assert
                    assert result == "統合テスト成功"
                    mock_load_env.assert_called_once()
                    mock_groq_class.assert_called_once_with(api_key="test-key")
                    mock_client.audio.transcriptions.create.assert_called_once()

                finally:
                    os.unlink(temp_path)

    def test_full_workflow_api_key_missing(self):
        """異常系: APIキー不足時の完全なワークフロー"""
        # Arrange
        with patch('external_service.groq_api.load_env_variables') as mock_load_env:
            mock_load_env.return_value = {}

            # Act & Assert
            with pytest.raises(ValueError, match="GROQ_API_KEYが未設定です"):
                setup_groq_client()


# エラーハンドリングとロギングの詳細テスト
class TestErrorHandlingAndLogging:
    """エラーハンドリングとログ出力の詳細テスト"""

    @pytest.fixture
    def mock_config(self):
        """テスト用設定データ"""
        return {
            'WHISPER': {
                'MODEL': 'whisper-large-v3',
                'PROMPT': 'テスト用プロンプト',
                'LANGUAGE': 'ja'
            }
        }

    @pytest.fixture
    def mock_client(self):
        """モックGroqクライアント"""
        client = Mock()
        transcription = Mock()
        transcription.text = "テスト文字起こし結果"
        client.audio.transcriptions.create.return_value = transcription
        return client

    def test_detailed_error_logging(self, mock_config, mock_client, caplog):
        """詳細なエラーログ出力の確認"""
        # Arrange
        caplog.set_level(logging.ERROR)
        mock_client.audio.transcriptions.create.side_effect = Exception("Detailed API Error")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            # Act
            result = transcribe_audio(temp_path, mock_config, mock_client)

            # Assert
            assert result is None
            assert "文字起こしエラー" in caplog.text
            assert "Detailed API Error" in caplog.text
            assert "デバッグ情報取得エラー" not in caplog.text

        finally:
            os.unlink(temp_path)

    def test_debug_info_collection_error(self, mock_config, mock_client, caplog):
        """デバッグ情報収集時のエラー処理"""
        # Arrange
        caplog.set_level(logging.ERROR)
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")

        # configの一部を破損させてデバッグ情報取得でエラーを発生させる
        broken_config = Mock()
        broken_config.get.side_effect = Exception("Config access error")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            # Act
            result = transcribe_audio(temp_path, broken_config, mock_client)

            # Assert
            assert result is None
            assert "デバッグ情報取得エラー" in caplog.text

        finally:
            os.unlink(temp_path)
