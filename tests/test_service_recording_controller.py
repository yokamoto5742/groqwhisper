import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from configparser import ConfigParser
from service_recording_controller import RecordingController



@pytest.fixture
def mock_config():
    config = ConfigParser()
    config['WHISPER'] = {'USE_PUNCTUATION': 'True'}
    config['KEYS'] = {'TOGGLE_RECORDING': 'F7'}
    config['RECORDING'] = {'AUTO_STOP_TIMER': '60'}
    config['CLIPBOARD'] = {'PASTE_DELAY': '0.1'}
    return config


@pytest.fixture
def mock_recorder():
    recorder = Mock()
    recorder.is_recording = False
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
        'update_status_label': Mock(),
        'update_record_button': Mock()
    }


@pytest.fixture
def mock_notification_callback():
    return Mock()


@pytest.fixture
def mock_tk():
    with patch('tkinter.Tk') as mock:
        mock_root = Mock()
        mock.return_value = mock_root
        yield mock_root


@pytest.fixture
def controller(mock_config, mock_recorder, mock_client, mock_replacements,
               mock_ui_callbacks, mock_notification_callback, mock_tk):
    controller = RecordingController(
        master=mock_tk,
        config=mock_config,
        recorder=mock_recorder,
        client=mock_client,
        replacements=mock_replacements,
        ui_callbacks=mock_ui_callbacks,
        notification_callback=mock_notification_callback
    )
    return controller


def test_init(controller):
    assert controller.use_punctuation is True
    assert controller.use_comma is True
    assert controller.recording_timer is None
    assert controller.five_second_timer is None
    assert controller.cancel_processing is None
    assert controller.processing_thread is None


def test_start_recording(controller):
    controller.start_recording()

    # レコーディングの開始が呼ばれたことを確認
    assert controller.recorder.start_recording.called
    controller.ui_callbacks['update_record_button'].assert_called_with(True)
    assert "音声入力中" in controller.ui_callbacks['update_status_label'].call_args[0][0]


def test_stop_recording(controller):
    # レコーディング状態を模擬
    controller.recorder.is_recording = True
    controller.recording_timer = Mock()
    controller.five_second_timer = "dummy_timer"

    controller.stop_recording()

    # タイマーがキャンセルされたことを確認
    assert controller.recording_timer.cancel.called
    controller.master.after_cancel.assert_called_with("dummy_timer")
    assert controller.recorder.stop_recording.called


def test_transcribe_audio_frames(controller):
    frames = [b'dummy_audio_data']
    sample_rate = 44100

    with patch('service_recording_controller.save_audio') as mock_save_audio, \
            patch('service_recording_controller.transcribe_audio') as mock_transcribe_audio, \
            patch('os.path.exists') as mock_exists, \
            patch('os.unlink') as mock_unlink:
        mock_save_audio.return_value = 'temp.wav'
        mock_transcribe_audio.return_value = 'テスト文字起こし'
        mock_exists.return_value = True

        controller.transcribe_audio_frames(frames, sample_rate)

        # 各メソッドが正しく呼ばれたことを確認
        mock_save_audio.assert_called_once_with(frames, sample_rate, controller.config)
        mock_transcribe_audio.assert_called_once()
        mock_unlink.assert_called_once_with('temp.wav')


def test_handle_error(controller):
    error_msg = "テストエラー"
    controller.recorder.is_recording = True

    controller._handle_error(error_msg)

    # エラーハンドリングの確認
    controller.show_notification.assert_called_with("エラー", error_msg)
    controller.ui_callbacks['update_status_label'].assert_called_with(
        f"{controller.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
    )
    controller.ui_callbacks['update_record_button'].assert_called_with(False)
    controller.recorder.stop_recording.assert_called_once()


@patch('time.sleep')
def test_cleanup(mock_sleep, controller):  # mock_sleepパラメータを追加
    # モックの設定
    controller.recorder.is_recording = True
    controller.recording_timer = Mock()
    controller.five_second_timer = "dummy_timer"

    controller.cleanup()

    assert controller.recorder.stop_recording.called
    assert controller.recording_timer.cancel.called
    controller.master.after_cancel.assert_called_with("dummy_timer")


def test_auto_stop_recording(controller):
    controller.auto_stop_recording()
    controller.master.after.assert_called_with(0, controller._auto_stop_recording_ui)


def test_auto_stop_recording_ui(controller):
    controller.master.quit = Mock()
    controller.recorder.stop_recording.return_value = ([], 44100)  # frames, sample_rate

    controller._auto_stop_recording_ui()

    controller.show_notification.assert_called_with("自動停止", "アプリケーションを終了します")
    controller.master.after.assert_called_with(1000, controller.master.quit)
