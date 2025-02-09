import pytest
from unittest.mock import Mock, patch
import tkinter as tk
from service_keyboard_handler import KeyboardHandler


@pytest.fixture
def mock_tk():
    mock = Mock(spec=tk.Tk)
    mock.after = Mock()
    return mock


@pytest.fixture
def mock_config():
    return {
        'KEYS': {
            'TOGGLE_RECORDING': 'f2',
            'EXIT_APP': 'f4',
            'TOGGLE_PUNCTUATION': 'f3'
        }
    }


@pytest.fixture
def mock_callbacks():
    return {
        'toggle_recording': Mock(),
        'toggle_punctuation': Mock(),
        'close_application': Mock()
    }


@pytest.fixture
def keyboard_handler(mock_tk, mock_config, mock_callbacks):
    with patch('keyboard.on_press_key'):
        handler = KeyboardHandler(
            mock_tk,
            mock_config,
            mock_callbacks['toggle_recording'],
            mock_callbacks['toggle_punctuation'],
            mock_callbacks['close_application']
        )
        return handler


def test_init_registers_keyboard_listeners(mock_tk, mock_config, mock_callbacks):
    with patch('keyboard.on_press_key') as mock_on_press_key:
        KeyboardHandler(
            mock_tk,
            mock_config,
            mock_callbacks['toggle_recording'],
            mock_callbacks['toggle_punctuation'],
            mock_callbacks['close_application']
        )

        assert mock_on_press_key.call_count == 3
        assert mock_on_press_key.call_args_list[0][0][0] == mock_config['KEYS']['TOGGLE_RECORDING']
        assert mock_on_press_key.call_args_list[1][0][0] == mock_config['KEYS']['EXIT_APP']
        assert mock_on_press_key.call_args_list[2][0][0] == mock_config['KEYS']['TOGGLE_PUNCTUATION']


def test_handle_toggle_recording_key(keyboard_handler, mock_tk):
    mock_event = Mock()
    keyboard_handler._handle_toggle_recording_key(mock_event)
    mock_tk.after.assert_called_once_with(0, keyboard_handler._toggle_recording)


def test_handle_exit_key(keyboard_handler, mock_tk):
    mock_event = Mock()
    keyboard_handler._handle_exit_key(mock_event)
    mock_tk.after.assert_called_once_with(0, keyboard_handler._close_application)


def test_handle_toggle_punctuation_key(keyboard_handler, mock_tk):
    mock_event = Mock()
    keyboard_handler._handle_toggle_punctuation_key(mock_event)
    mock_tk.after.assert_called_once_with(0, keyboard_handler._toggle_punctuation)


def test_cleanup(keyboard_handler):
    with patch('keyboard.unhook_all') as mock_unhook:
        keyboard_handler.cleanup()
        mock_unhook.assert_called_once()


def test_cleanup_handles_exception(keyboard_handler):
    with patch('keyboard.unhook_all', side_effect=Exception('Test error')):
        with patch('logging.error') as mock_logging:
            keyboard_handler.cleanup()
            mock_logging.assert_called_once()


def test_setup_keyboard_listeners_handles_exception(mock_tk, mock_config, mock_callbacks):
    with patch('keyboard.on_press_key', side_effect=Exception('Test error')):
        with pytest.raises(Exception):
            with patch('logging.error') as mock_logging:
                KeyboardHandler(
                    mock_tk,
                    mock_config,
                    mock_callbacks['toggle_recording'],
                    mock_callbacks['toggle_punctuation'],
                    mock_callbacks['close_application']
                )
                mock_logging.assert_called_once()
