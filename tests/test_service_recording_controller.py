import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any
import threading
import tempfile
from configparser import ConfigParser
from service_recording_controller import RecordingController


# Tkinterのモック
@pytest.fixture
def mock_tk():
    with patch('tkinter.Tk') as mock:
        yield mock.return_value


@pytest.fixture
def mock_config() -> ConfigParser:
    config = ConfigParser()
    config['WHISPER'] = {
        'USE_PUNCTUATION': 'true',
        'USE_COMMA': 'true'
    }
    config['RECORDING'] = {
        'AUTO_STOP_TIMER': '60'
    }
    config['KEYS'] = {
        'TOGGLE_RECORDING': 'F6',
        'EXIT_APP': 'F12'
    }
    return config


@pytest.fixture
def mock_recorder():
    recorder = Mock()
    recorder.is_recording = False
    recorder.record = Mock()
    recorder.stop_recording = Mock(return_value=([], 44100))
    return recorder


@pytest.fixture
def mock_client():
    return Mock()


@pytest.fixture
def mock_replacements():
    return {'old': 'new'}


@pytest.fixture
def mock_ui_callbacks():
    return {
        'update_record_button': Mock(),
        'update_status_label': Mock(),
        'append_transcription': Mock()
    }


@pytest.fixture
def mock_notification_callback():
    return Mock()


@pytest.fixture
def recording_controller(
        mock_tk,
        mock_config,
        mock_recorder,
        mock_client,
        mock_replacements,
        mock_ui_callbacks,
        mock_notification_callback
):
    controller = RecordingController(
        mock_tk,
        mock_config,
        mock_recorder,
        mock_client,
        mock_replacements,
        mock_ui_callbacks,
        mock_notification_callback
    )
    return controller


def test_init(recording_controller):
    """初期化のテスト"""
    assert recording_controller.use_punctuation is True
    assert recording_controller.use_comma is True
    assert recording_controller.recording_timer is None
    assert recording_controller.five_second_timer is None
    assert recording_controller.five_second_notification_shown is False


def test_start_recording(recording_controller, mock_ui_callbacks):
    """録音開始のテスト"""
    with patch('threading.Thread') as mock_thread:
        with patch('threading.Timer') as mock_timer:
            recording_controller.start_recording()

            assert recording_controller.recorder.start_recording.called
            mock_ui_callbacks['update_record_button'].assert_called_with(True)
            assert mock_thread.called
            assert mock_timer.called


def test_stop_recording(recording_controller, mock_ui_callbacks):
    """録音停止のテスト"""
    recording_controller.recording_timer = threading.Timer(60, lambda: None)
    recording_controller.recording_timer.start()
    recording_controller.five_second_timer = "dummy_timer"

    with patch.object(recording_controller.master, 'after_cancel') as mock_after_cancel:
        recording_controller.stop_recording()

        assert not recording_controller.recording_timer.is_alive()
        mock_after_cancel.assert_called_once()
        assert recording_controller.five_second_timer is None


@patch('service_recording_controller.save_audio')
@patch('service_recording_controller.transcribe_audio')
@patch('service_recording_controller.replace_text')
@patch('service_recording_controller.copy_and_paste_transcription')
def test_process_audio(
        mock_copy_paste,
        mock_replace,
        mock_transcribe,
        mock_save,
        recording_controller,
        mock_ui_callbacks
):
    """音声処理のテスト"""
    # モックの戻り値を設定
    mock_save.return_value = tempfile.mktemp()
    mock_transcribe.return_value = "テスト音声"
    mock_replace.return_value = "変換後テキスト"

    frames = [b'dummy_audio_data']
    sample_rate = 44100

    # master.afterのモックを追加し、即時実行するように設定
    def execute_callback(delay, callback, *args):
        if callback:
            callback(*args) if args else callback()

    with patch.object(recording_controller.master, 'after') as mock_after:
        mock_after.side_effect = execute_callback
        recording_controller.process_audio(frames, sample_rate)

    # 各モックの呼び出しを確認
    assert mock_save.called
    assert mock_transcribe.called
    assert mock_replace.called
    assert mock_copy_paste.called


def test_show_five_second_notification(recording_controller):
    """5秒前通知のテスト"""
    recording_controller.recorder.is_recording = True
    recording_controller.five_second_notification_shown = False

    recording_controller.show_five_second_notification()

    recording_controller.show_notification.assert_called_once_with(
        "自動停止",
        "あと5秒で音声入力を停止します"
    )
    assert recording_controller.five_second_notification_shown is True


def test_auto_stop_recording(recording_controller):
    """自動停止のテスト"""
    with patch.object(recording_controller.master, 'after') as mock_after:
        recording_controller.auto_stop_recording()
        mock_after.assert_called_once_with(0, recording_controller._auto_stop_recording_ui)


def test_cleanup(recording_controller):
    """クリーンアップのテスト"""
    # タイマーをモック化
    mock_timer = Mock()
    mock_timer.is_alive = Mock(return_value=True)  # Trueに変更
    mock_timer.cancel = Mock()

    recording_controller.recording_timer = mock_timer
    recording_controller.five_second_timer = "dummy_timer"

    with patch.object(recording_controller.master, 'after_cancel') as mock_after_cancel:
        recording_controller.cleanup()

        # タイマーがキャンセルされたことを確認
        assert mock_timer.cancel.called
        assert recording_controller.five_second_timer is None
        mock_after_cancel.assert_called_once()