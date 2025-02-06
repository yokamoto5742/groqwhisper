import tkinter as tk
from typing import Optional, Dict, Any, Callable


class UIComponents:
    def __init__(
            self,
            master: tk.Tk,
            config: Dict[str, Any],
            callbacks: Dict[str, Callable]
    ):
        self.master = master
        self.config = config
        self._toggle_recording = callbacks['toggle_recording']
        self._toggle_punctuation = callbacks['toggle_punctuation']
        self.status_label: Optional[tk.Label] = None
        self.punctuation_button: Optional[tk.Button] = None
        self.record_button: Optional[tk.Button] = None

    def setup_ui(self, version: str) -> None:
        self.master.title(f'音声入力メモ v{version}')

        window_width = int(self.config['WINDOW'].get('width', 300))
        window_height = int(self.config['WINDOW'].get('height', 200))
        self.master.geometry(f"{window_width}x{window_height}")

        self.record_button = tk.Button(
            self.master,
            text='音声入力開始',
            command=self._toggle_recording
        )
        self.record_button.pack(pady=5)

        self.punctuation_button = tk.Button(
            self.master,
            text=f'現在句読点あり:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}',
            command=self._toggle_punctuation
        )
        self.punctuation_button.pack(pady=5)

        self.status_label = tk.Label(
            self.master,
            text=f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止 {self.config['KEYS']['EXIT_APP']}キーで終了"
        )
        self.status_label.pack(pady=5)

    def update_record_button(self, is_recording: bool) -> None:
        self.record_button.config(
            text='音声入力停止' if is_recording else '音声入力開始'
        )

    def update_status_label(self, text: str) -> None:
        self.status_label.config(text=text)

    def update_punctuation_button(self, use_punctuation: bool) -> None:
        self.punctuation_button.config(
            text=f'現在句読点{"あり" if use_punctuation else "なし"}:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}'
        )
