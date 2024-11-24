import threading
import logging
import pyautogui
import pyperclip
import os
import sys
from typing import Dict

from decorator_safe_operation import safe_operation

logger = logging.getLogger(__name__)

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
                    continue  # 無効な行をスキップして続行
    except IOError as e:
        logger.error(f"置換ファイルの読み込み中にエラーが発生しました: {e}")
        return {}  # 空の辞書を返して続行
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        return {}  # 予期せぬエラーの場合も空の辞書を返して続行

    return replacements

@safe_operation
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

    replaced_text = replace_text(text, replacements)
    logging.info(f"テキスト置換完了")
    pyperclip.copy(replaced_text)
    logging.info(f"クリップボードコピー完了")

    paste_delay = float(config['CLIPBOARD'].get('PASTE_DELAY', 0.5))

    def paste_text():
        pyautogui.hotkey('ctrl', 'v')
        logging.info("貼り付け完了")

    threading.Timer(paste_delay, paste_text).start()
