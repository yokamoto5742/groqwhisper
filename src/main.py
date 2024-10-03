import tkinter as tk
import logging
from typing import Dict, Any

from audio_recorder import AudioRecorder
from config.config import load_config
from gui import AudioRecorderGUI
from text_processing import load_replacements
from transcription import setup_groq_client
from log_rotation import setup_logging

VERSION = "1.0.2"
LAST_UPDATED = "2024/10/03"

logger = logging.getLogger(__name__)


def main() -> None:
    try:
        config: Dict[str, Any] = load_config()
        setup_logging(config)
    except FileNotFoundError:
        print("設定ファイルが見つかりません。")
        return
    except ValueError as e:
        print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
        return

    logger.info(f"アプリケーションを開始します。バージョン: {VERSION}")

    try:
        recorder = AudioRecorder(config)
    except Exception as e:
        logger.error(f"AudioRecorderの初期化中にエラーが発生しました: {e}")
        return

    try:
        client = setup_groq_client()
    except Exception as e:
        logger.error(f"Groqクライアントのセットアップ中にエラーが発生しました: {e}")
        return

    try:
        replacements = load_replacements()
    except FileNotFoundError:
        logger.error("置換ファイルが見つかりません。")
        return
    except ValueError as e:
        logger.error(f"置換ファイルの読み込み中にエラーが発生しました: {e}")
        return

    root = tk.Tk()
    try:
        app = AudioRecorderGUI(root, config, recorder, client, replacements, VERSION)
        root.protocol("WM_DELETE_WINDOW", app.close_application)
        root.mainloop()
    except Exception as e:
        logger.error(f"GUIの初期化中またはメインループ中にエラーが発生しました: {e}")
    finally:
        root.destroy()

    logger.info("アプリケーションを終了します。")


if __name__ == "__main__":
    main()
