import os
import threading
from typing import Dict
import logging

import pyautogui
import pyperclip

# プロジェクトのルートディレクトリへの相対パスを取得
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# ロガーの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_replacements(file_path: str = 'replacements.txt') -> Dict[str, str]:
    """置換ルールをファイルから読み込む。"""
    replacements = {}
    full_path = os.path.join(PROJECT_ROOT, 'config', file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    old, new = line.strip().split(',')
                    replacements[old] = new
                except ValueError:
                    logger.warning(f"Invalid line in replacements file: {line.strip()}")
    except FileNotFoundError:
        logger.error(f"Replacements file not found: {full_path}")
    except IOError as e:
        logger.error(f"Error reading replacements file: {e}")
    return replacements


def replace_text(text: str, replacements: Dict[str, str]) -> str:
    """テキスト内の特定の文字列を置換する。"""
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def copy_and_paste_transcription(
    text: str,
    replacements: Dict[str, str],
    config: Dict[str, Dict[str, str]]
) -> None:
    """テキストを置換してクリップボードにコピーし、貼り付ける。"""
    if not text:
        logger.warning("Empty text provided, skipping copy and paste operation.")
        return

    replaced_text = replace_text(text, replacements)
    pyperclip.copy(replaced_text)
    logger.info("Text copied to clipboard.")

    try:
        paste_delay = float(config['CLIPBOARD']['PASTE_DELAY'])
    except KeyError:
        logger.error("PASTE_DELAY not found in config. Using default value of 0.5 seconds.")
        paste_delay = 0.5
    except ValueError:
        logger.error("Invalid PASTE_DELAY value in config. Using default value of 0.5 seconds.")
        paste_delay = 0.5

    def paste_text():
        try:
            pyautogui.hotkey('ctrl', 'v')
            logger.info("Text pasted successfully.")
        except pyautogui.FailSafeException:
            logger.error("PyAutoGUI failsafe triggered. Mouse movement interrupted.")
        except Exception as e:
            logger.error(f"Error occurred while pasting text: {e}")

    threading.Timer(paste_delay, paste_text).start()
    logger.info(f"Paste operation scheduled after {paste_delay} seconds.")
