import logging
import threading
import time
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
import pyperclip

logger = logging.getLogger(__name__)

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


class ClipboardPaster:
    def __init__(self):
        self.backup_clipboard = ""

    def backup_clipboard_content(self) -> bool:
        try:
            self.backup_clipboard = pyperclip.paste()
            return True
        except Exception as e:
            logging.error(f"クリップボードバックアップエラー: {str(e)}")
            return False

    def restore_clipboard_content(self) -> bool:
        try:
            if self.backup_clipboard is not None:
                pyperclip.copy(self.backup_clipboard)
                return True
            return True
        except Exception as e:
            logging.error(f"クリップボードリストアエラー: {str(e)}")
            return False

    def get_active_window_info(self) -> Tuple[Optional[int], Optional[str]]:
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd == 0:
                return None, None

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
        try:
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            time.sleep(0.01)

            user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.01)

            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)

            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            return True

        except Exception as e:
            logging.error(f"keybd_event API実行エラー: {str(e)}")
            return False

    def send_paste_message(self) -> bool:
        try:
            hwnd, window_title = self.get_active_window_info()
            if hwnd is None:
                logging.error("アクティブウィンドウが見つかりません")
                return False

            result = user32.SendMessageW(hwnd, WM_PASTE, 0, 0)

            def enum_child_proc(child_hwnd, lparam):
                try:
                    user32.SendMessageW(child_hwnd, WM_PASTE, 0, 0)
                except:
                    pass
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            enum_proc = WNDENUMPROC(enum_child_proc)
            user32.EnumChildWindows(hwnd, enum_proc, 0)

            logging.info(f"WM_PASTEメッセージ送信完了: {window_title}")
            return True

        except Exception as e:
            logging.error(f"WM_PASTEメッセージ送信エラー: {str(e)}")
            return False

    def paste_text(self, text: str) -> bool:
        try:
            if not self.backup_clipboard_content():
                logging.warning("クリップボードバックアップに失敗しました")

            pyperclip.copy(text)
            time.sleep(0.1)

            paste_methods = [
                ("keybd_event", self.send_ctrl_v_keybd_event),
                ("WM_PASTE", self.send_paste_message),
            ]

            for method_name, method_func in paste_methods:
                try:
                    if method_func():
                        success = True
                        break
                except Exception as e:
                    logging.error(f"貼り付け方法 {method_name} でエラー: {str(e)}")
                    continue
            else:
                logging.error("すべての貼り付け方法が失敗しました")
                success = False

            time.sleep(0.15)
            self.restore_clipboard_content()

            return success

        except Exception as e:
            logging.error(f"ペーストエラー: {str(e)}")
            try:
                self.restore_clipboard_content()
            except:
                pass
            return False


clipboard_paster = ClipboardPaster()


def safe_clipboard_copy(text: str) -> bool:
    max_retries = 2
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

    logging.error("クリップボードコピーが最大試行回数後に失敗しました")
    return False


def safe_paste_text() -> bool:
    with _paste_lock:
        try:
            current_text = pyperclip.paste()
            if not current_text:
                logging.warning("クリップボードが空です")
                return False

            return clipboard_paster.paste_text(current_text)

        except Exception as e:
            logging.error(f"貼り付けエラー: {str(e)}")
            return False


def is_paste_available() -> bool:
    try:
        if not hasattr(user32, 'keybd_event'):
            logging.error("keybd_event関数が見つかりません")
            return False

        if not hasattr(user32, 'GetForegroundWindow'):
            logging.error("GetForegroundWindow関数が見つかりません")
            return False

        hwnd = user32.GetForegroundWindow()
        if hwnd == 0:
            logging.warning("現在アクティブなウィンドウがありません")

        return True

    except Exception as e:
        logging.error(f"貼り付け機能利用不可: {str(e)}")
        return False

