import pytest
from unittest.mock import Mock, MagicMock, patch
import tkinter as tk
from configparser import ConfigParser
from app_window import AudioRecorderGUI


@pytest.fixture
def mock_config():
    config = ConfigParser()
    config['OPTIONS'] = {
        'START_MINIMIZED': 'False'
    }
    config['WHISPER'] = {
        'USE_PUNCTUATION': 'True',
        'USE_COMMA': 'True'
    }
    return config


@pytest.fixture
def mock_master():
    master = MagicMock(spec=tk.Tk)
    master.iconify = Mock()
    master.quit = Mock()
    return master


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
def gui(mock_master, mock_config, mock_recorder, mock_client, mock_replacements):
    with patch('app_window.UIComponents') as mock_ui, \
            patch('app_window.KeyboardHandler') as mock_keyboard, \
            patch('app_window.RecordingController') as mock_recording, \
            patch('app_window.NotificationManager') as mock_notification:
        gui = AudioRecorderGUI(
            mock_master,
            mock_config,
            mock_recorder,
            mock_client,
            mock_replacements,
            "1.0.0"
        )

        # RecordingControllerの属性を設定
        gui.recording_controller.use_punctuation = True
        gui.recording_controller.use_comma = True

        return gui


def test_initialize_with_start_minimized(mock_master, mock_config, mock_recorder, mock_client, mock_replacements):
    mock_config['OPTIONS']['START_MINIMIZED'] = 'True'

    with patch('app_window.UIComponents'), \
            patch('app_window.KeyboardHandler'), \
            patch('app_window.RecordingController'), \
            patch('app_window.NotificationManager'):
        AudioRecorderGUI(mock_master, mock_config, mock_recorder, mock_client, mock_replacements, "1.0.0")

    mock_master.iconify.assert_called_once()


def test_toggle_recording(gui):
    gui.toggle_recording()
    gui.recording_controller.toggle_recording.assert_called_once()


def test_toggle_punctuation(gui):
    with patch('app_window.save_config') as mock_save:
        initial_state = gui.recording_controller.use_punctuation
        gui.toggle_punctuation()

        assert gui.recording_controller.use_punctuation == (not initial_state)
        gui.ui_components.update_punctuation_button.assert_called_with(not initial_state)
        mock_save.assert_called_once_with(gui.config)


def test_toggle_comma(gui):
    with patch('app_window.save_config') as mock_save:
        initial_state = gui.recording_controller.use_comma
        gui.toggle_comma()

        assert gui.recording_controller.use_comma == (not initial_state)
        gui.ui_components.update_comma_button.assert_called_with(not initial_state)
        mock_save.assert_called_once_with(gui.config)


def test_copy_to_clipboard(gui):
    mock_text = "テストテキスト"
    gui.ui_components.get_transcription_text.return_value = mock_text

    gui.copy_to_clipboard()

    gui.ui_components.get_transcription_text.assert_called_once()
    gui.recording_controller.safe_copy_and_paste.assert_called_once_with(mock_text)


def test_clear_text(gui):
    gui.clear_text()
    gui.ui_components.clear_transcription_text.assert_called_once()


def test_close_application(gui):
    gui.close_application()

    gui.recording_controller.cleanup.assert_called_once()
    gui.keyboard_handler.cleanup.assert_called_once()
    gui.notification_manager.cleanup.assert_called_once()
    gui.master.quit.assert_called_once()
