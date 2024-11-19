import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from service_notification import NotificationManager


@pytest.fixture
def mock_tk():
    with patch('tkinter.Tk') as mock:
        yield mock


@pytest.fixture
def mock_toplevel():
    with patch('tkinter.Toplevel') as mock:
        yield mock


@pytest.fixture
def config():
    return {
        'KEYS': {
            'TOGGLE_RECORDING': 'Ctrl+Space'
        }
    }


@pytest.fixture
def notification_manager(mock_tk, config):
    master = mock_tk()
    manager = NotificationManager(master, config)
    return manager


def test_init(notification_manager, config):
    assert notification_manager.config == config
    assert notification_manager.current_popup is None


def test_show_timed_message(notification_manager, mock_toplevel):
    title = "テストタイトル"
    message = "テストメッセージ"

    notification_manager.show_timed_message(title, message)

    # Toplevelが作成されたことを確認
    mock_toplevel.assert_called_once()

    # 設定が正しく適用されたことを確認
    popup = mock_toplevel.return_value
    popup.title.assert_called_with(title)
    popup.attributes.assert_called_with('-topmost', True)


def test_show_error_message(notification_manager):
    with patch.object(notification_manager, 'show_timed_message') as mock_show:
        notification_manager.show_error_message("エラー", "エラーメッセージ")
        mock_show.assert_called_with("エラー: エラー", "エラーメッセージ", 2000)


def test_show_status_message(notification_manager):
    message = "テスト中"
    mock_status_label = MagicMock()

    # ステータスラベルをモック
    notification_manager.master.children = {'status_label': mock_status_label}

    notification_manager.show_status_message(message)

    # masterのafterメソッドが呼ばれることを確認
    notification_manager.master.after.assert_called_once()

    # ステータステキストが正しく更新されることを確認
    expected_text = f"{notification_manager.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止 {message}"
    notification_manager._update_status_label(expected_text)
    mock_status_label.config.assert_called_with(text=expected_text)


def test_cleanup_with_popup(notification_manager):
    # モックのポップアップを設定
    mock_popup = MagicMock()
    notification_manager.current_popup = mock_popup

    notification_manager.cleanup()

    # ポップアップが破棄されたことを確認
    mock_popup.destroy.assert_called_once()


def test_cleanup_without_popup(notification_manager):
    notification_manager.current_popup = None
    notification_manager.cleanup()  # エラーが発生しないことを確認


def test_destroy_popup_error_handling(notification_manager):
    # TclErrorを発生させるモックポップアップを作成
    mock_popup = MagicMock()
    mock_popup.destroy.side_effect = tk.TclError()
    notification_manager.current_popup = mock_popup

    with patch('logging.error') as mock_logging:  # ログ出力をモック化
        notification_manager._destroy_popup()  # エラーがキャッチされることを確認

    # destroyメソッドが呼ばれたことを確認
    mock_popup.destroy.assert_called_once()
    # エラーがログに記録されたことを確認
    mock_logging.assert_not_called()  # TclErrorは正常な終了として扱われる
    # current_popupがNoneに設定されていることを確認
    assert notification_manager.current_popup is None
