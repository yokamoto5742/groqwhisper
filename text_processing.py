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
        # PyInstallerでビルドされた実行ファイルの場合
        base_path = sys._MEIPASS
    else:
        # 通常のPythonスクリプトとして実行される場合
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
                    continue  # 空行をスキップ
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
        logger.warning("空のテキストが提供されました。コピー＆ペースト操作をスキップします。")
        return

    replaced_text = replace_text(text, replacements)
    pyperclip.copy(replaced_text)
    logger.info("テキストをクリップボードにコピーしました。")

    try:
        paste_delay = float(config['CLIPBOARD']['PASTE_DELAY'])
    except KeyError:
        logger.error("設定にPASTE_DELAYが見つかりません。")
        paste_delay = 0.5
    except ValueError:
        logger.error("設定のPASTE_DELAY値が無効です。")
        paste_delay = 0.5

    def paste_text():
        try:
            pyautogui.hotkey('ctrl', 'v')
            logger.info("テキストを正常に貼り付けました。")
        except pyautogui.FailSafeException:
            logger.error("PyAutoGUIのフェイルセーフがトリガーされました。")
        except Exception as e:
            logger.error(f"テキストの貼り付け中にエラーが発生しました: {e}")

    threading.Timer(paste_delay, paste_text).start()
    logger.info(f"{paste_delay}秒後に貼り付け操作をスケジュールしました。")
