import logging
import os
import sys
import threading
import time
from typing import Dict

import pyautogui
import pyperclip

logger = logging.getLogger(__name__)

# グローバルロック（クリップボード競合防止）
_clipboard_lock = threading.Lock()
_paste_lock = threading.Lock()


def get_replacements_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'replacements.txt')


def load_replacements() -> Dict[str, str]:
    replacements = {}
    file_path = get_replacements_path()
    logging.info(f"置換ルールファイルのパス: {file_path}")

    try:
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()
            logging.info(f"置換ルールファイルの行数: {len(lines)}")

            for line_number, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    old, new = line.split(',')
                    replacements[old.strip()] = new.strip()
                    logging.debug(f"置換ルール読み込み - {line_number}行目: '{old.strip()}' → '{new.strip()}'")
                except ValueError:
                    logging.error(f"置換ファイルの{line_number}行目に無効な行があります: {line}")
                    continue

            logging.info(f"有効な置換ルールの総数: {len(replacements)}")
            if len(replacements) > 0:
                logging.debug("読み込んだ置換ルール:")
                for old, new in replacements.items():
                    logging.debug(f"  '{old}' → '{new}'")

    except IOError as e:
        logging.error(f"置換ファイルの読み込み中にエラーが発生しました: {e}")
        return {}
    except Exception as e:
        logging.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
        return {}

    return replacements


def replace_text(text: str, replacements: Dict[str, str]) -> str:
    if not text:
        logging.error("入力テキストが空です")
        return ""

    if not replacements:
        logging.warning("置換ルールが空です")
        return text

    try:
        result = text
        logging.info(f"テキスト置換開始 - 文字数: {len(text)}")

        for old, new in replacements.items():
            if old in result:
                before_replace = result
                result = result.replace(old, new)
                if before_replace != result:
                    logging.debug(f"置換実行: '{old}' → '{new}'")

        logging.info("テキスト置換完了")
        return result

    except Exception as e:
        logging.error(f"テキスト置換中にエラーが発生: {str(e)}", exc_info=True)
        return text


def safe_clipboard_copy(text: str) -> bool:
    """安全なクリップボードコピー"""
    with _clipboard_lock:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pyperclip.copy(text)

                # コピーが成功したか検証
                time.sleep(0.05)  # 短い待機
                copied_text = pyperclip.paste()
                if copied_text == text:
                    logging.info("クリップボードコピー完了")
                    return True
                else:
                    logging.warning(f"クリップボードコピー検証失敗 (試行 {attempt + 1}/{max_retries})")

            except Exception as e:
                logging.error(f"クリップボードコピー中にエラー (試行 {attempt + 1}/{max_retries}): {str(e)}")

            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # 指数バックオフ

        logging.error("クリップボードコピーが最大試行回数後も失敗しました")
        return False


def safe_paste_text() -> bool:
    """安全なペースト実行"""
    with _paste_lock:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # より安全なキー送信設定
                pyautogui.FAILSAFE = False  # フェールセーフを一時的に無効化
                pyautogui.PAUSE = 0.01  # 短い間隔

                # Ctrl+Vを送信
                pyautogui.hotkey('ctrl', 'v')
                logging.info("ペースト実行完了")
                return True

            except pyautogui.FailSafeException:
                logging.warning(f"PyAutoGUIフェールセーフが作動 (試行 {attempt + 1}/{max_retries})")

            except Exception as e:
                logging.error(f"ペースト実行中にエラー (試行 {attempt + 1}/{max_retries}): {str(e)}")

            finally:
                pyautogui.FAILSAFE = True  # フェールセーフを再有効化

            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # 指数バックオフ

        logging.error("ペースト実行が最大試行回数後も失敗しました")
        return False


def paste_text():
    """後方互換性のためのラッパー関数"""
    try:
        return safe_paste_text()
    except Exception as e:
        logging.error(f"貼り付け処理でエラー: {str(e)}", exc_info=True)
        return False


def copy_and_paste_transcription(
        text: str,
        replacements: Dict[str, str],
        config: Dict[str, Dict[str, str]]
):
    """安全なコピー&ペースト実行"""
    if not text:
        logging.warning("空のテキスト")
        return

    try:
        # テキスト置換
        replaced_text = replace_text(text, replacements)
        if not replaced_text:
            logging.error("テキスト置換結果が空です")
            return

        # 安全なクリップボードコピー
        if not safe_clipboard_copy(replaced_text):
            raise Exception("クリップボードへのコピーに失敗しました")

        # ペースト遅延の取得と適用
        try:
            paste_delay = float(config['CLIPBOARD'].get('PASTE_DELAY', 0.1))
            # 最小/最大遅延の制限
            paste_delay = max(0.05, min(paste_delay, 2.0))
        except (ValueError, KeyError):
            paste_delay = 0.1
            logging.warning("PASTE_DELAY設定が無効です。デフォルト値(0.1)を使用します")

        # 遅延後にペースト実行
        def delayed_paste():
            try:
                time.sleep(paste_delay)
                if not safe_paste_text():
                    logging.error("ペースト実行に失敗しました")
            except Exception as paste_error:
                logging.error(f"遅延ペースト中にエラー: {str(paste_error)}", exc_info=True)

        # 別スレッドでペースト実行（UIをブロックしない）
        paste_thread = threading.Thread(target=delayed_paste, daemon=True)
        paste_thread.start()

    except Exception as e:
        logging.error(f"コピー&ペースト処理でエラー: {str(e)}", exc_info=True)
        raise


# 緊急時のクリップボード復旧関数
def emergency_clipboard_recovery():
    """クリップボードが破損した場合の復旧処理"""
    try:
        with _clipboard_lock:
            # クリップボードをクリア
            pyperclip.copy("")
            time.sleep(0.1)

            # 簡単なテキストでテスト
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


# モジュール初期化時の設定
def _initialize_module():
    """モジュール初期化時の設定"""
    try:
        # PyAutoGUIの設定
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = True

        # クリップボードの初期化テスト
        test_result = emergency_clipboard_recovery()
        if not test_result:
            logging.warning("クリップボード初期化テストに失敗しました")

    except Exception as e:
        logging.error(f"モジュール初期化中にエラー: {str(e)}")


# モジュール読み込み時に初期化実行
_initialize_module()
