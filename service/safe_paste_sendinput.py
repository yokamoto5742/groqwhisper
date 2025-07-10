import logging
import threading
import time
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
import pyperclip

logger = logging.getLogger(__name__)

# ペースト用のロック
_paste_lock = threading.Lock()

# Windows API定数
VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
WM_PASTE = 0x0302
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

# Windows API関数の取得
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class NoAdminPaster:
    """管理者権限不要の貼り付けクラス"""

    def __init__(self):
        self.backup_clipboard = ""

    def backup_clipboard_content(self) -> bool:
        """現在のクリップボード内容をバックアップ"""
        try:
            self.backup_clipboard = pyperclip.paste()
            logging.debug("クリップボードバックアップ完了")
            return True
        except Exception as e:
            logging.error(f"クリップボードバックアップエラー: {str(e)}")
            return False

    def restore_clipboard_content(self) -> bool:
        """クリップボード内容をリストア"""
        try:
            if self.backup_clipboard is not None:
                pyperclip.copy(self.backup_clipboard)
                logging.debug("クリップボードリストア完了")
                return True
            return True
        except Exception as e:
            logging.error(f"クリップボードリストアエラー: {str(e)}")
            return False

    def get_active_window_info(self) -> Tuple[Optional[int], Optional[str]]:
        """アクティブウィンドウの情報を取得"""
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return None, None

            # ウィンドウタイトルを取得
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return hwnd, ""

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            window_title = buffer.value

            return hwnd, window_title

        except Exception as e:
            logging.error(f"アクティブウィンドウ情報取得エラー: {str(e)}")
            return None, None

    def send_ctrl_v_keybd_event(self) -> bool:
        """keybd_event APIを使用してCtrl+Vを送信（管理者権限不要）"""
        try:
            # Ctrl キーダウン
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            time.sleep(0.01)

            # V キーダウン
            user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.01)

            # V キーアップ
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)

            # Ctrl キーアップ
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            logging.info("keybd_event APIによるCtrl+V送信完了")
            return True

        except Exception as e:
            logging.error(f"keybd_event API実行エラー: {str(e)}")
            return False

    def send_paste_message(self) -> bool:
        """WM_PASTEメッセージを直接送信"""
        try:
            hwnd, window_title = self.get_active_window_info()
            if hwnd is None:
                logging.error("アクティブウィンドウが見つかりません")
                return False

            # WM_PASTEメッセージを送信
            result = user32.SendMessageW(hwnd, WM_PASTE, 0, 0)

            # 子ウィンドウ（エディットコントロール）にも送信を試行
            def enum_child_proc(child_hwnd, lparam):
                try:
                    user32.SendMessageW(child_hwnd, WM_PASTE, 0, 0)
                except:
                    pass
                return True

            # 子ウィンドウを列挙してWM_PASTEを送信
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            enum_proc = WNDENUMPROC(enum_child_proc)
            user32.EnumChildWindows(hwnd, enum_proc, 0)

            logging.info(f"WM_PASTEメッセージ送信完了: {window_title}")
            return True

        except Exception as e:
            logging.error(f"WM_PASTEメッセージ送信エラー: {str(e)}")
            return False

    def send_ctrl_v_postmessage(self) -> bool:
        """PostMessageでCtrl+Vを送信"""
        try:
            hwnd, window_title = self.get_active_window_info()
            if hwnd is None:
                logging.error("アクティブウィンドウが見つかりません")
                return False

            # Ctrl キーダウン
            user32.PostMessageW(hwnd, WM_KEYDOWN, VK_CONTROL, 0)
            time.sleep(0.01)

            # V キーダウン
            user32.PostMessageW(hwnd, WM_KEYDOWN, VK_V, 0)
            time.sleep(0.01)

            # V キーアップ
            user32.PostMessageW(hwnd, WM_KEYUP, VK_V, 0)
            time.sleep(0.01)

            # Ctrl キーアップ
            user32.PostMessageW(hwnd, WM_KEYUP, VK_CONTROL, 0)

            logging.info(f"PostMessage Ctrl+V送信完了: {window_title}")
            return True

        except Exception as e:
            logging.error(f"PostMessage実行エラー: {str(e)}")
            return False

    def paste_text_no_admin(self, text: str) -> bool:
        """管理者権限不要でテキストを貼り付け"""
        try:
            # クリップボードバックアップ
            if not self.backup_clipboard_content():
                logging.warning("クリップボードバックアップに失敗しましたが続行します")

            # テキストをクリップボードにコピー
            pyperclip.copy(text)

            # クリップボード更新を確実にする
            time.sleep(0.1)

            # 複数の方法を順次試行
            paste_methods = [
                ("keybd_event", self.send_ctrl_v_keybd_event),
                ("WM_PASTE", self.send_paste_message),
                ("PostMessage", self.send_ctrl_v_postmessage)
            ]

            for method_name, method_func in paste_methods:
                try:
                    logging.info(f"貼り付け方法を試行: {method_name}")
                    if method_func():
                        logging.info(f"貼り付け成功: {method_name}")
                        success = True
                        break
                except Exception as e:
                    logging.error(f"貼り付け方法 {method_name} でエラー: {str(e)}")
                    continue
            else:
                logging.error("すべての貼り付け方法が失敗しました")
                success = False

            # クリップボードをリストア
            time.sleep(0.15)
            self.restore_clipboard_content()

            return success

        except Exception as e:
            logging.error(f"管理者権限不要ペーストエラー: {str(e)}")
            # エラー時でもクリップボードをリストア試行
            try:
                self.restore_clipboard_content()
            except:
                pass
            return False


# グローバルインスタンス
_no_admin_paster = NoAdminPaster()


def safe_clipboard_copy(text: str) -> bool:
    """安全なクリップボードコピー"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            copied_text = pyperclip.paste()
            if copied_text == text:
                logging.info("クリップボードコピー完了")
                return True
            else:
                logging.warning(f"クリップボードコピー検証失敗 (試行 {attempt + 1}/{max_retries})")
        except Exception as e:
            logging.error(f"クリップボードコピー中にエラー (試行 {attempt + 1}/{max_retries}): {str(e)}")

        if attempt < max_retries - 1:
            time.sleep(0.1 * (attempt + 1))

    logging.error("クリップボードコピーが最大試行回数後も失敗しました")
    return False


def safe_paste_text_no_admin() -> bool:
    """管理者権限不要の安全な貼り付け"""
    with _paste_lock:
        try:
            # 現在のクリップボード内容を取得
            current_text = pyperclip.paste()
            if not current_text:
                logging.warning("クリップボードが空です")
                return False

            # 管理者権限不要で貼り付け実行
            return _no_admin_paster.paste_text_no_admin(current_text)

        except Exception as e:
            logging.error(f"管理者権限不要貼り付けエラー: {str(e)}")
            return False


def is_paste_available() -> bool:
    """貼り付け機能が利用可能かチェック"""
    try:
        # 基本的なWindows API関数の存在確認
        if not hasattr(user32, 'keybd_event'):
            logging.error("keybd_event関数が見つかりません")
            return False

        if not hasattr(user32, 'GetForegroundWindow'):
            logging.error("GetForegroundWindow関数が見つかりません")
            return False

        # アクティブウィンドウの取得テスト
        hwnd = user32.GetForegroundWindow()
        if hwnd == 0:
            logging.warning("現在アクティブなウィンドウがありません")

        logging.info("貼り付け機能利用可能（管理者権限不要）")
        return True

    except Exception as e:
        logging.error(f"貼り付け機能利用不可: {str(e)}")
        return False


def emergency_clipboard_recovery() -> bool:
    """クリップボード復旧機能"""
    try:
        pyperclip.copy("")
        time.sleep(0.1)

        test_text = "test"
        pyperclip.copy(test_text)
        time.sleep(0.1)

        if pyperclip.paste() == test_text:
            logging.info("クリップボード復旧成功")
            return True
        else:
            logging.error("クリップボード復旧失敗")
            return False

    except Exception as e:
        logging.error(f"クリップボード復旧中にエラー: {str(e)}")
        return False
