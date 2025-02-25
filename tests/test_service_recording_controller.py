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
    config['PATHS'] = {
        'TEMP_DIR': '/tmp/test',
        'CLEANUP_MINUTES': '60'
    }
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
    with patch('os.makedirs'):
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
    assert controller.temp_dir == '/tmp/test'
    assert controller.cleanup_minutes == 60


def test_start_recording(controller):
    controller.start_recording()

    assert controller.recorder.start_recording.called
    controller.ui_callbacks['update_record_button'].assert_called_with(True)
    assert "音声入力中" in controller.ui_callbacks['update_status_label'].call_args[0][0]


def test_stop_recording(controller):
    controller.recorder.is_recording = True
    controller.recording_timer = Mock()
    controller.five_second_timer = "dummy_timer"

    controller.stop_recording()

    assert controller.recording_timer.cancel.called
    controller.master.after_cancel.assert_called_with("dummy_timer")
    assert controller.recorder.stop_recording.called


def test_transcribe_audio_frames(controller):
    frames = [b'dummy_audio_data']
    sample_rate = 44100

    with patch('service_recording_controller.save_audio') as mock_save_audio, \
            patch('service_recording_controller.transcribe_audio') as mock_transcribe_audio:
        mock_save_audio.return_value = 'temp.wav'
        mock_transcribe_audio.return_value = 'テスト文字起こし'

        controller.transcribe_audio_frames(frames, sample_rate)

        mock_save_audio.assert_called_once_with(frames, sample_rate, controller.config)
        mock_transcribe_audio.assert_called_once()


def test_handle_error(controller):
    error_msg = "テストエラー"
    controller.recorder.is_recording = True

    controller._handle_error(error_msg)

    controller.show_notification.assert_called_with("エラー", error_msg)
    controller.ui_callbacks['update_status_label'].assert_called_with(
        f"{controller.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
    )
    controller.ui_callbacks['update_record_button'].assert_called_with(False)
    controller.recorder.stop_recording.assert_called_once()


@patch('time.sleep')
@patch('threading.Thread')
@patch('os.path.getmtime')
@patch('glob.glob')
@patch('os.remove')
def test_cleanup(mock_remove, mock_glob, mock_getmtime, mock_thread, mock_sleep, controller):
    # モックの設定
    controller.recorder.is_recording = True
    controller.recording_timer = Mock()
    controller.five_second_timer = "dummy_timer"
    controller.processing_thread = Mock()
    controller.processing_thread.is_alive.side_effect = [True, True, False]

    mock_glob.return_value = ['test1.wav', 'test2.wav']
    mock_getmtime.return_value = time.time() - 3600  # 1時間前

    controller.cleanup()

    assert controller.recorder.stop_recording.called
    assert controller.recording_timer.cancel.called
    controller.master.after_cancel.assert_called_with("dummy_timer")


def test_auto_stop_recording(controller):
    controller.auto_stop_recording()
    controller.master.after.assert_called_with(0, controller._auto_stop_recording_ui)


def test_auto_stop_recording_ui(controller):
    controller.master.quit = Mock()
    controller.recorder.stop_recording.return_value = ([], 44100)

    controller._auto_stop_recording_ui()

    controller.show_notification.assert_called_with("自動停止", "アプリケーションを終了します")
    controller.master.after.assert_called_with(1000, controller.master.quit)


@patch('threading.Thread')
def test_wait_for_processing(mock_thread, controller):
    # スレッドのモック設定
    mock_processing_thread = Mock()
    mock_processing_thread.is_alive.side_effect = [True, False]
    controller.processing_thread = mock_processing_thread

    controller._wait_for_processing()

    # 処理スレッドのjoinが呼ばれたことを確認
    mock_processing_thread.join.assert_called_with(timeout=5.0)
    controller.ui_callbacks['update_status_label'].assert_called_with("処理完了待機中...")
