import tkinter as tk

from audio_recorder import AudioRecorder
from config import load_config
from log_rotation import setup_logging
from gui import AudioRecorderGUI
from text_processing import load_replacements
from transcription import setup_groq_client

VERSION = "1.0.4"
LAST_UPDATED = "2024/10/06"


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
    main()
