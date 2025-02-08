import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from configparser import ConfigParser
from app_window import VoiceInputManager


@pytest.fixture
def config():
    config = ConfigParser()
    config['OPTIONS'] = {
        'START_MINIMIZED': 'True'
    }
    config['WHISPER'] = {
        'USE_PUNCTUATION': 'False',
        'USE_COMMA': 'False'
    }
    return config


@pytest.fixture
def mock_recorder():
    return Mock()


@pytest.fixture
def mock_client():
    return Mock()


@pytest.fixture
def mock_replacements():
    return {}


@pytest.fixture
def mock_tk_root():
    with patch('tkinter.Tk') as mock:
        root = mock.return_value
        root.iconify = Mock()
        root.quit = Mock()
        yield root


@pytest.fixture
def voice_input_manager(mock_tk_root, config, mock_recorder, mock_client, mock_replacements):
    with patch('app_window.UIComponents') as mock_ui, \
            patch('app_window.KeyboardHandler') as mock_keyboard, \
            patch('app_window.RecordingController') as mock_recording, \
            patch('app_window.NotificationManager') as mock_notification:
        # RecordingControllerの初期状態を設定
        mock_recording_instance = mock_recording.return_value
        mock_recording_instance.use_punctuation = False
        mock_recording_instance.use_comma = False

        manager = VoiceInputManager(
            mock_tk_root,
            config,
            mock_recorder,
            mock_client,
            mock_replacements,
            "1.0.0"
        )
        return manager


class TestVoiceInputManager:
    def test_init_starts_minimized(self, voice_input_manager, mock_tk_root):
        """START_MINIMIZEDがTrueの場合、ウィンドウが最小化されることを確認"""
        mock_tk_root.iconify.assert_called_once()

    def test_toggle_punctuation(self, voice_input_manager, config):
        """句読点の切り替えが正しく動作することを確認"""
        # 初期状態の確認
        assert not voice_input_manager.recording_controller.use_punctuation

        # 句読点を有効化
        voice_input_manager.toggle_punctuation()

        # 状態の確認
        assert voice_input_manager.recording_controller.use_punctuation
        assert voice_input_manager.recording_controller.use_comma
        assert config['WHISPER']['USE_PUNCTUATION'] == 'True'
        assert config['WHISPER']['USE_COMMA'] == 'True'

        # UIの更新が呼ばれたことを確認
        voice_input_manager.ui_components.update_punctuation_button.assert_called_with(True)

    def test_close_application(self, voice_input_manager, mock_tk_root):
        """アプリケーションの終了処理が正しく実行されることを確認"""
        voice_input_manager.close_application()

        # 各コンポーネントのクリーンアップが呼ばれたことを確認
        voice_input_manager.recording_controller.cleanup.assert_called_once()
        voice_input_manager.keyboard_handler.cleanup.assert_called_once()
        voice_input_manager.notification_manager.cleanup.assert_called_once()
        mock_tk_root.quit.assert_called_once()

    def test_toggle_recording(self, voice_input_manager):
        """録音の切り替えが正しく動作することを確認"""
        voice_input_manager.toggle_recording()
        voice_input_manager.recording_controller.toggle_recording.assert_called_once()

    @pytest.mark.parametrize("start_minimized", [True, False])
    def test_init_window_state(self, mock_tk_root, config, mock_recorder,
                               mock_client, mock_replacements, start_minimized):
        """START_MINIMIZEDの設定に応じて、正しい初期状態になることを確認"""
        config['OPTIONS']['START_MINIMIZED'] = str(start_minimized)

        with patch('app_window.UIComponents'), \
                patch('app_window.KeyboardHandler'), \
                patch('app_window.RecordingController'), \
                patch('app_window.NotificationManager'):

            VoiceInputManager(mock_tk_root, config, mock_recorder,
                              mock_client, mock_replacements, "1.0.0")

            if start_minimized:
                mock_tk_root.iconify.assert_called_once()
            else:
                mock_tk_root.iconify.assert_not_called()
