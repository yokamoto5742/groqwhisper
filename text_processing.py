import os
import threading
from typing import Dict
import logging
import pyautogui
import pyperclip

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
logger = logging.getLogger(__name__)


def load_replacements(file_path: str = 'replacements.txt') -> Dict[str, str]:
    """置換ルールをファイルから読み込む。"""
    replacements = {}
    full_path = r'C:\Users\yokam\PycharmProjects\groqwhisper\replacements.txt'
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    old, new = line.strip().split(',')
                    replacements[old] = new
                except ValueError:
                    logger.warning(f"置換ファイルに無効な行があります: {line.strip()}")
    except FileNotFoundError:
        logger.error(f"置換ファイルが見つかりません: {full_path}")
        raise
    except IOError as e:
        logger.error(f"置換ファイルの読み込み中にエラーが発生しました: {e}")
        raise
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
        logger.warning("空のテキストが提供されました。コピー＆ペースト操作をスキップします。")
        return

    replaced_text = replace_text(text, replacements)
    pyperclip.copy(replaced_text)
    logger.info("テキストをクリップボードにコピーしました。")

    try:
        paste_delay = float(config['CLIPBOARD']['PASTE_DELAY'])
    except KeyError:
        logger.error("設定にPASTE_DELAYが見つかりません。デフォルト値の0.5秒を使用します。")
        paste_delay = 0.5
    except ValueError:
        logger.error("設定のPASTE_DELAY値が無効です。デフォルト値の0.5秒を使用します。")
        paste_delay = 0.5

    def paste_text():
        try:
            pyautogui.hotkey('ctrl', 'v')
            logger.info("テキストを正常に貼り付けました。")
        except pyautogui.FailSafeException:
            logger.error("PyAutoGUIのフェイルセーフがトリガーされました。マウスの動きが中断されました。")
        except Exception as e:
            logger.error(f"テキストの貼り付け中にエラーが発生しました: {e}")

    threading.Timer(paste_delay, paste_text).start()
    logger.info(f"{paste_delay}秒後に貼り付け操作をスケジュールしました。")
