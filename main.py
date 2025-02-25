import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback
import logging

from config_manager import load_config
from service_audio_recorder import AudioRecorder
from log_rotation import setup_logging
from app_window import VoiceInputManager
from service_text_processing import load_replacements
from service_transcription import setup_groq_client
from version import VERSION


def main():
    try:
        config = load_config()
        setup_logging(config)
        logging.info("アプリケーションを開始します")

        recorder = AudioRecorder(config)
        client = setup_groq_client()
        replacements = load_replacements()

        root = tk.Tk()
        app = VoiceInputManager(root, config, recorder, client, replacements, VERSION)
        root.protocol("WM_DELETE_WINDOW", app.close_application)
        root.mainloop()

    except Exception as e:
        error_msg = f"予期せぬエラーが発生しました:\n{str(e)}\n\n{traceback.format_exc()}"
        logging.error(error_msg)

        try:
            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(error_msg)

            if 'root' not in locals():
                root = tk.Tk()
            root.withdraw()
            messagebox.showerror("エラー", f"予期せぬエラーが発生しました。\n\n{str(e)}")
            os.startfile('error_log.txt')

        except Exception as dialog_error:
            print(f"エラーダイアログ表示中に例外が発生: {str(dialog_error)}", file=sys.stderr)

        finally:
            sys.exit(1)


if __name__ == "__main__":
    main()
