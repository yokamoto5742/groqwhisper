import os
import threading
from typing import Dict

import pyautogui
import pyperclip

# プロジェクトのルートディレクトリへの相対パスを取得
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load_replacements(file_path: str = 'replacements.txt') -> Dict[str, str]:
    """置換ルールをファイルから読み込む。"""
    replacements = {}
    full_path = os.path.join(PROJECT_ROOT, 'config', file_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        for line in f:
            old, new = line.strip().split(',')
            replacements[old] = new
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
    if text:
        replaced_text = replace_text(text, replacements)
        pyperclip.copy(replaced_text)
        paste_delay = float(config['CLIPBOARD']['PASTE_DELAY'])
        threading.Timer(
            paste_delay,
            lambda: pyautogui.hotkey('ctrl', 'v')
        ).start()
