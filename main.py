import tkinter as tk
from tkinter import messagebox
import traceback
import multiprocessing

from audio_recorder import AudioRecorder
from config import load_config
from log_rotation import setup_logging
from gui import AudioRecorderGUI
from text_processing import load_replacements
from transcription import setup_groq_client

VERSION = "1.0.6"
LAST_UPDATED = "2024/10/21"


def main():
    config = load_config()
    setup_logging(config)
    recorder = AudioRecorder(config)
    client = setup_groq_client()
    replacements = load_replacements()

    root = tk.Tk()
    app = AudioRecorderGUI(root, config, recorder, client, replacements, VERSION)
    root.protocol("WM_DELETE_WINDOW", app.close_application)
    root.mainloop()


if __name__ == "__main__":
    try:
        multiprocessing.freeze_support()
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
