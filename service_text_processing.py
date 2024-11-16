import threading
import traceback
from functools import wraps
from typing import Dict
import logging
import pyautogui
import pyperclip
import os
import sys

logger = logging.getLogger(__name__)

def safe_operation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{func.__name__}でエラーが発生: {str(e)}")
            logging.error(traceback.format_exc())
    return wrapper

def get_replacements_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'replacements.txt')

def load_replacements() -> Dict[str, str]:
    replacements = {}
    file_path = get_replacements_path()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    old, new = line.split(',')
                    replacements[old.strip()] = new.strip()
                except ValueError:
                    logger.warning(f"置換ファイルの{line_number}行目に無効な行があります: {line}")
    except FileNotFoundError:
        logger.error(f"置換ファイルが見つかりません: {file_path}")
        raise
    except IOError as e:
        logger.error(f"置換ファイルの読み込み中にエラーが発生しました: {e}")
        raise
    return replacements

def replace_text(text: str, replacements: Dict[str, str]) -> str:
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


@safe_operation
def copy_and_paste_transcription(
        text: str,
        replacements: Dict[str, str],
        config: Dict[str, Dict[str, str]]
) -> None:
    if not text:
        logging.warning("空のテキスト")
        return

    try:
        replaced_text = replace_text(text, replacements)
        logging.info(f"テキスト置換完了")
        pyperclip.copy(replaced_text)
        logging.info(f"クリップボードコピー完了")

        paste_delay = float(config['CLIPBOARD'].get('PASTE_DELAY', 0.5))

        def paste_text():
            try:
                pyautogui.hotkey('ctrl', 'v')
                logging.info("貼り付け完了")
            except Exception as e:
                logging.error(f"貼り付けエラー: {str(e)}")

        threading.Timer(paste_delay, paste_text).start()

    except Exception as e:
        logging.error(f"テキスト処理エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
