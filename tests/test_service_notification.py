import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from service_notification import NotificationManager


@pytest.fixture
def mock_tk():
    with patch('tkinter.Tk') as mock:
        # モックTkインスタンスの作成
        mock_instance = MagicMock()
        mock_instance.children = {}
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def config():
    return {
        'KEYS': {
            'TOGGLE_RECORDING': 'Ctrl+Space'
        }
    }


@pytest.fixture
def notification_manager(mock_tk, config):
    return NotificationManager(mock_tk, config)


def test_show_timed_message(notification_manager):
    # TopLevelウィンドウのモック化
    with patch('tkinter.Toplevel') as mock_toplevel:
        mock_window = MagicMock()
        mock_toplevel.return_value = mock_window

        notification_manager.show_timed_message("テストタイトル", "テストメッセージ")

        # Topレベルウィンドウが作成されたことを確認
        mock_toplevel.assert_called_once()
        # タイトルが設定されたことを確認
        mock_window.title.assert_called_with("テストタイトル")
        # topmostが設定されたことを確認
        mock_window.attributes.assert_called_with('-topmost', True)


def test_show_error_message(notification_manager):
    with patch.object(notification_manager, 'show_timed_message') as mock_show:
        notification_manager.show_error_message("エラータイトル", "エラーメッセージ")
        mock_show.assert_called_with("エラー: エラータイトル", "エラーメッセージ", 3000)


def test_show_status_message(notification_manager, mock_tk):
    # ステータスラベルのモック作成
    mock_label = MagicMock()
    mock_tk.children['status_label'] = mock_label

    notification_manager.show_status_message("テスト中")

    expected_text = "Ctrl+Spaceキーで音声入力開始/停止 テスト中"
    # afterメソッドが呼ばれたことを確認
    mock_tk.after.assert_called()
    # コールバック関数を実行
    mock_tk.after.call_args[0][1]()
    # ラベルのテキストが更新されたことを確認
    mock_label.config.assert_called_with(text=expected_text)


def test_destroy_popup_with_tcl_error(notification_manager):
    mock_popup = MagicMock()
    mock_popup.destroy.side_effect = tk.TclError
    notification_manager.current_popup = mock_popup

    notification_manager._destroy_popup()

    # エラーが発生しても正常に処理され、current_popupがNoneになることを確認
    assert notification_manager.current_popup is None


def test_update_status_label_no_label(notification_manager, mock_tk):
    # status_labelが存在しない場合のテスト
    mock_tk.children = {}

    # エラーが発生しないことを確認
    notification_manager._update_status_label("テストメッセージ")


def test_cleanup(notification_manager):
    # current_popupのモック作成
    mock_popup = MagicMock()
    notification_manager.current_popup = mock_popup

    notification_manager.cleanup()

    # destroyメソッドが呼ばれたことを確認
    mock_popup.destroy.assert_called_once()