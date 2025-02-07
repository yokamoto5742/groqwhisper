import sys
import tkinter as tk
from tkinter import messagebox
import traceback
import multiprocessing
import logging

from config_manager import load_config
from service_audio_recorder import AudioRecorder
from log_rotation import setup_logging
from app_window import VoiceInputManager
from service_text_processing import load_replacements
from service_transcription import setup_groq_client
from version import VERSION


def main():
    config = load_config()
    setup_logging(config)
    recorder = AudioRecorder(config)
    client = setup_groq_client()
    replacements = load_replacements()

    root = tk.Tk()
    app = VoiceInputManager(root, config, recorder, client, replacements, VERSION)
    root.protocol("WM_DELETE_WINDOW", app.close_application)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"予期せぬエラーが発生しました:\n{str(e)}\n\n{traceback.format_exc()}"
        logging.error(error_msg)
        with open('error_log.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("エラー", f"エラーが発生しました。詳細は error_log.txt を確認してください。\n\n{str(e)}")
        sys.exit(1)
