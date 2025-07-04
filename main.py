import logging
import os
import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from app_window import VoiceInputManager
from config_manager import load_config
from external_service.groq_api import setup_groq_client
from log_rotation import setup_logging
from service.audio_recorder import AudioRecorder
from service.text_processing import load_replacements
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


if __name__ == "__main__":
    main()
