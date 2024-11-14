import pytest
from unittest.mock import Mock, patch
import tkinter as tk
from service_keyboard_handler import KeyboardHandler


@pytest.fixture
def mock_config():
    return {
        'KEYS': {
            'TOGGLE_RECORDING': 'f2',
            'EXIT_APP': 'f4',
            'TOGGLE_PUNCTUATION': 'f3',
            'TOGGLE_COMMA': 'f5'
        }
    }


@pytest.fixture
def mock_callbacks():
    return {
        'toggle_recording': Mock(),
        'toggle_punctuation': Mock(),
        'toggle_comma': Mock(),
        'close_application': Mock()
    }


@pytest.fixture
def mock_tk():
    mock = Mock(spec=tk.Tk)
    mock.after = Mock()
    return mock


@pytest.fixture
def keyboard_handler(mock_tk, mock_config, mock_callbacks):
    with patch('keyboard.on_press_key') as mock_on_press_key:
        handler = KeyboardHandler(
            master=mock_tk,
            config=mock_config,
            toggle_recording_callback=mock_callbacks['toggle_recording'],
            toggle_punctuation_callback=mock_callbacks['toggle_punctuation'],
            toggle_comma_callback=mock_callbacks['toggle_comma'],
            close_application_callback=mock_callbacks['close_application']
        )
        return handler, mock_on_press_key


def test_initialization(keyboard_handler, mock_config):
    handler, mock_on_press_key = keyboard_handler

    # キーボードリスナーが正しく設定されているか確認
    assert mock_on_press_key.call_count == 4
    mock_on_press_key.assert_any_call(
        mock_config['KEYS']['TOGGLE_RECORDING'],
        handler._handle_toggle_recording_key
    )
    mock_on_press_key.assert_any_call(
        mock_config['KEYS']['EXIT_APP'],
        handler._handle_exit_key
    )
    mock_on_press_key.assert_any_call(
        mock_config['KEYS']['TOGGLE_PUNCTUATION'],
        handler._handle_toggle_punctuation_key
    )
    mock_on_press_key.assert_any_call(
        mock_config['KEYS']['TOGGLE_COMMA'],
        handler._handle_toggle_comma_key
    )


def test_handle_toggle_recording_key(keyboard_handler, mock_tk, mock_callbacks):
    handler, _ = keyboard_handler
    mock_event = Mock()

    handler._handle_toggle_recording_key(mock_event)
    mock_tk.after.assert_called_once_with(0, mock_callbacks['toggle_recording'])


def test_handle_exit_key(keyboard_handler, mock_tk, mock_callbacks):
    handler, _ = keyboard_handler
    mock_event = Mock()

    handler._handle_exit_key(mock_event)
    mock_tk.after.assert_called_once_with(0, mock_callbacks['close_application'])


def test_handle_toggle_punctuation_key(keyboard_handler, mock_tk, mock_callbacks):
    handler, _ = keyboard_handler
    mock_event = Mock()

    handler._handle_toggle_punctuation_key(mock_event)
    mock_tk.after.assert_called_once_with(0, mock_callbacks['toggle_punctuation'])


def test_handle_toggle_comma_key(keyboard_handler, mock_tk, mock_callbacks):
    handler, _ = keyboard_handler
    mock_event = Mock()

    handler._handle_toggle_comma_key(mock_event)
    mock_tk.after.assert_called_once_with(0, mock_callbacks['toggle_comma'])


@patch('keyboard.unhook_all')
def test_cleanup_success(mock_unhook_all):
    KeyboardHandler.cleanup()
    mock_unhook_all.assert_called_once()


@patch('keyboard.unhook_all')
def test_cleanup_error(mock_unhook_all, caplog):
    mock_unhook_all.side_effect = Exception("テストエラー")

    KeyboardHandler.cleanup()

    assert "キーボードリスナーの解除中にエラーが発生しました" in caplog.text


@patch('keyboard.on_press_key')
def test_initialization_error(mock_on_press_key, mock_tk, mock_config, mock_callbacks):
    mock_on_press_key.side_effect = Exception("テストエラー")

    with pytest.raises(Exception) as exc_info:
        KeyboardHandler(
            master=mock_tk,
            config=mock_config,
            toggle_recording_callback=mock_callbacks['toggle_recording'],
            toggle_punctuation_callback=mock_callbacks['toggle_punctuation'],
            toggle_comma_callback=mock_callbacks['toggle_comma'],
            close_application_callback=mock_callbacks['close_application']
        )

    assert "テストエラー" in str(exc_info.value)
