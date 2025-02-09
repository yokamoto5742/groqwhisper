import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from configparser import ConfigParser
from app_window import VoiceInputManager
from copy import deepcopy
import os


@pytest.fixture
def config():
    """実際のConfig.iniから設定を読み込むfixture"""
    config = ConfigParser()

    # テスト実行時のカレントディレクトリにあるConfig.iniを読み込む
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Config.ini')
    if os.path.exists(config_path):
        config.read(config_path, encoding='utf-8')
    else:
        # Config.iniが存在しない場合はデフォルト値を設定
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
        mock_recording_instance.use_punctuation = config['WHISPER'].getboolean('USE_PUNCTUATION', False)
        mock_recording_instance.use_comma = config['WHISPER'].getboolean('USE_COMMA', False)

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
    def test_init_starts_minimized(self, voice_input_manager, mock_tk_root, config):
        """START_MINIMIZEDがTrueの場合、ウィンドウが最小化されることを確認"""
        original_config = deepcopy(config)
        try:
            mock_tk_root.iconify.assert_called_once()
        finally:
            # configを元の状態に復元
            self._restore_config(config, original_config)

    def test_toggle_punctuation(self, voice_input_manager, config):
        """句読点の切り替えが正しく動作することを確認"""
        original_config = deepcopy(config)
        try:
            # テスト用の初期状態を設定
            voice_input_manager.recording_controller.use_punctuation = False
            voice_input_manager.recording_controller.use_comma = False
            config['WHISPER']['USE_PUNCTUATION'] = 'False'
            config['WHISPER']['USE_COMMA'] = 'False'

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
        finally:
            # configとコントローラーの状態を復元
            self._restore_config_and_controller(config, original_config, voice_input_manager)

    def test_close_application(self, voice_input_manager, mock_tk_root, config):
        """アプリケーションの終了処理が正しく実行されることを確認"""
        original_config = deepcopy(config)
        try:
            voice_input_manager.close_application()

            # 各コンポーネントのクリーンアップが呼ばれたことを確認
            voice_input_manager.recording_controller.cleanup.assert_called_once()
            voice_input_manager.keyboard_handler.cleanup.assert_called_once()
            voice_input_manager.notification_manager.cleanup.assert_called_once()
            mock_tk_root.quit.assert_called_once()
        finally:
            self._restore_config(config, original_config)

    def test_toggle_recording(self, voice_input_manager, config):
        """録音の切り替えが正しく動作することを確認"""
        original_config = deepcopy(config)
        try:
            voice_input_manager.toggle_recording()
            voice_input_manager.recording_controller.toggle_recording.assert_called_once()
        finally:
            self._restore_config(config, original_config)

    @pytest.mark.parametrize("start_minimized", [True, False])
    def test_init_window_state(self, mock_tk_root, config, mock_recorder,
                               mock_client, mock_replacements, start_minimized):
        """START_MINIMIZEDの設定に応じて、正しい初期状態になることを確認"""
        original_config = deepcopy(config)
        try:
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
        finally:
            self._restore_config(config, original_config)

    def _restore_config(self, config, original_config):
        """configを元の状態に復元するヘルパーメソッド"""
        # 現在のconfigの全セクションをクリア
        for section in config.sections():
            config.remove_section(section)

        # original_configから全ての設定を復元
        for section in original_config.sections():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in original_config[section].items():
                config[section][key] = value

    def _restore_config_and_controller(self, config, original_config, voice_input_manager):
        """configとコントローラーの状態を復元するヘルパーメソッド"""
        self._restore_config(config, original_config)

        # コントローラーの状態も元に戻す
        use_punctuation = original_config['WHISPER'].getboolean('USE_PUNCTUATION', False)
        use_comma = original_config['WHISPER'].getboolean('USE_COMMA', False)
        voice_input_manager.recording_controller.use_punctuation = use_punctuation
        voice_input_manager.recording_controller.use_comma = use_comma
