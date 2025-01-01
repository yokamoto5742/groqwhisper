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
    logging.info(f"置換ルールファイルのパス: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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


@safe_operation
def replace_text(text: str, replacements: Dict[str, str]) -> str:
    if not text:
        logging.error("入力テキストが空です")
        return ""

    if not replacements:
        logging.warning("置換ルールが空です")
        return text

    try:
        result = text
        # 置換の開始時に1回だけログを出力
        logging.info(f"テキスト置換開始 - 文字数: {len(text)}")
        logging.info(f"置換ルール数: {len(replacements)}")

        # 個別の置換処理をデバッグレベルに変更
        for old, new in replacements.items():
            if old in result:
                before_replace = result
                result = result.replace(old, new)
                if before_replace != result:
                    logging.debug(f"置換実行: '{old}' → '{new}'")

        # 最終結果のログ出力
        logging.info("テキスト置換完了")
        return result

    except Exception as e:
        logging.error(f"テキスト置換中にエラーが発生: {str(e)}", exc_info=True)
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
        # テキスト置換は1回だけ実行
        replaced_text = replace_text(text, replacements)
        if not replaced_text:
            logging.error("テキスト置換結果が空です")
            return

        # クリップボードへのコピー
        pyperclip.copy(replaced_text)
        logging.info("クリップボードコピー完了")

        paste_delay = float(config['CLIPBOARD'].get('PASTE_DELAY', 0.5))

        def paste_text():
            try:
                pyautogui.hotkey('ctrl', 'v')
                logging.info("貼り付け完了")
            except Exception as e:
                logging.error(f"貼り付け処理でエラー: {str(e)}", exc_info=True)

        # 貼り付け処理のタイマー設定
        threading.Timer(paste_delay, paste_text).start()

    except Exception as e:
        logging.error(f"コピー&ペースト処理でエラー: {str(e)}", exc_info=True)
        raise


# service_recording_controller.py のui_updateメソッドも修正

@safe_operation
def ui_update(self, text: str) -> None:
    if not text:
        logging.warning("空のテキストが渡されました")
        return

    # テキストをUIに追加
    self.ui_callbacks['append_transcription'](text)

    # 貼り付け処理を遅延実行
    paste_delay = int(float(self.config['CLIPBOARD'].get('PASTE_DELAY', 0.5)) * 1000)
    self.master.after(paste_delay, lambda: self.copy_and_paste(text))


@safe_operation
def copy_and_paste(self, text: str) -> None:
    # テキスト置換とクリップボード操作は1回だけ実行
    copy_and_paste_transcription(text, self.replacements, self.config)
