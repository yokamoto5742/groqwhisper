import tkinter as tk
import pyautogui
from typing import Optional, Dict, Any, Callable

from service_text_editor import ReplacementsEditor


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
        self.punctuation_status_label: Optional[tk.Label] = None
        self.punctuation_button: Optional[tk.Button] = None
        self.record_button: Optional[tk.Button] = None
        self.history_button: Optional[tk.Button] = None
        self.replace_button: Optional[tk.Button] = None
        self.close_button: Optional[tk.Button] = None

    def setup_ui(self, version: str):
        self.master.title(f'音声入力メモ v{version}')

        window_width = int(self.config['WINDOW'].get('width', 350))
        window_height = int(self.config['WINDOW'].get('height', 350))
        self.master.geometry(f"{window_width}x{window_height}")

        # 録音ボタン
        self.record_button = tk.Button(
            self.master,
            text=f'音声入力開始',
            command=self._toggle_recording,
            width=20
        )
        self.record_button.pack(pady=10)

        # 句読点ボタン
        self.punctuation_button = tk.Button(
            self.master,
            text=f'句読点切替え:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}',
            command=self._toggle_punctuation,
            width=20
        )
        self.punctuation_button.pack(pady=5)

        # 句読点状態ラベル
        self.punctuation_status_label = tk.Label(
            self.master,
            text='現在句読点あり'
        )
        self.punctuation_status_label.pack(pady=5)

        # クリップボード履歴ボタン
        self.history_button = tk.Button(
            self.master,
            text='クリップボード履歴',
            command=self.open_clipboard_history,
            width=20
        )
        self.history_button.pack(pady=5)

        # テキスト置換登録ボタン
        self.replace_button = tk.Button(
            self.master,
            text='テキスト置換登録',
            command=self.open_replacements_editor,
            width=20
        )
        self.replace_button.pack(pady=5)

        # 終了ボタン
        self.close_button = tk.Button(
            self.master,
            text=f'閉じる:{self.config["KEYS"]["EXIT_APP"]}',
            command=self.master.quit,
            width=20
        )
        self.close_button.pack(pady=5)

        # 一般情報ステータスラベル
        self.status_label = tk.Label(
            self.master,
            text=f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
        )
        self.status_label.pack(pady=10)

    def update_record_button(self, is_recording: bool):
        self.record_button.config(
            text=f'音声入力{"停止" if is_recording else "開始"}:{self.config["KEYS"]["TOGGLE_RECORDING"]}'
        )

    def update_status_label(self, text: str):
        self.status_label.config(text=text)

    def update_punctuation_button(self, use_punctuation: bool):
        self.punctuation_status_label.config(
            text=f'現在句読点{"あり" if use_punctuation else "なし"}'
        )

    @staticmethod
    def open_clipboard_history():
        pyautogui.hotkey('win', 'v')

    def open_replacements_editor(self):
        ReplacementsEditor(self.master, self.config)
