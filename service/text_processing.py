import logging
import os
import sys
import threading
import time
from typing import Dict

import pyperclip

# 管理者権限不要のペースト機能をインポート
from service.safe_paste_sendinput import safe_paste_text_no_admin, safe_clipboard_copy, is_paste_available

logger = logging.getLogger(__name__)

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

            logging.info(f"置換ルールの総数: {len(replacements)}")
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


def safe_paste_text() -> bool:
    """管理者権限不要の安全な貼り付け（pyAutoGUI完全削除版）"""
    with _paste_lock:
        # 貼り付け機能の利用可能性チェック
        if not is_paste_available():
            logging.error("貼り付け機能が利用できません")
            return False

        # 管理者権限不要の貼り付け実行
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if safe_paste_text_no_admin():
                    logging.info("管理者権限不要貼り付け完了")
                    return True
                else:
                    logging.warning(f"貼り付け失敗 (試行 {attempt + 1}/{max_retries})")

            except Exception as e:
                logging.error(f"貼り付け中にエラー (試行 {attempt + 1}/{max_retries}): {str(e)}")

            if attempt < max_retries - 1:
                time.sleep(0.2)  # 短い待機

        logging.error("すべての貼り付け試行が失敗しました")
        return False


def copy_and_paste_transcription(
        text: str,
        replacements: Dict[str, str],
        config: Dict[str, Dict[str, str]]
):
    """管理者権限不要のコピー&ペースト処理（pyAutoGUI完全削除版）"""
    if not text:
        logging.warning("空のテキスト")
        return

    try:
        replaced_text = replace_text(text, replacements)
        if not replaced_text:
            logging.error("テキスト置換結果が空です")
            return

        # クリップボードにコピー
        if not safe_clipboard_copy(replaced_text):
            raise Exception("クリップボードへのコピーに失敗しました")

        try:
            paste_delay_str = config['CLIPBOARD'].get('PASTE_DELAY', '0.2')
            # コメントが含まれている場合は最初の部分のみ使用
            paste_delay_clean = paste_delay_str.split('#')[0].split(';')[0].strip()
            paste_delay = float(paste_delay_clean)
            paste_delay = max(0.05, min(paste_delay, 1.0))
            logging.debug(f"PASTE_DELAY設定値: {paste_delay}")
        except (ValueError, KeyError, AttributeError) as e:
            paste_delay = 0.2
            logging.warning(
                f"PASTE_DELAY設定が無効です ('{config.get('CLIPBOARD', {}).get('PASTE_DELAY', 'None')}'): {str(e)}。デフォルト値{paste_delay}を使用します")

        def delayed_paste():
            try:
                time.sleep(paste_delay)
                if not safe_paste_text():
                    logging.error("管理者権限不要貼り付け実行に失敗しました")
            except Exception as paste_error:
                logging.error(f"遅延ペースト中にエラー: {str(paste_error)}", exc_info=True)

        paste_thread = threading.Thread(target=delayed_paste, daemon=True)
        paste_thread.start()

    except Exception as e:
        logging.error(f"コピー&ペースト処理でエラー: {str(e)}", exc_info=True)
        raise


def emergency_clipboard_recovery():
    """クリップボード復旧機能"""
    try:
        with _clipboard_lock:
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


def _initialize_module():
    """モジュール初期化処理（pyAutoGUI完全削除版）"""
    try:
        # 貼り付け機能利用可能性をチェック
        if is_paste_available():
            logging.info("管理者権限不要貼り付け機能初期化完了")
        else:
            logging.error("貼り付け機能初期化失敗")

        # クリップボード初期化テスト
        test_result = emergency_clipboard_recovery()
        if not test_result:
            logging.warning("クリップボード初期化テストに失敗しました")

    except Exception as e:
        logging.error(f"モジュール初期化中にエラー: {str(e)}")


# モジュール初期化実行
_initialize_module()