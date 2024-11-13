import tkinter as tk
from typing import Optional, Dict, Any, Callable


class UIComponents:
    def __init__(
            self,
            master: tk.Tk,
            config: Dict[str, Any],
            toggle_recording_callback: Callable,
            copy_callback: Callable,
            clear_callback: Callable,
            toggle_comma_callback: Callable,
            toggle_punctuation_callback: Callable
    ):
        self.master: tk.Tk = master
        self.config: Dict[str, Any] = config

        self._toggle_recording = toggle_recording_callback
        self._copy_to_clipboard = copy_callback
        self._clear_text = clear_callback
        self._toggle_comma = toggle_comma_callback
        self._toggle_punctuation = toggle_punctuation_callback

        self.status_label: Optional[tk.Label] = None
        self.punctuation_button: Optional[tk.Button] = None
        self.comma_button: Optional[tk.Button] = None
        self.clear_button: Optional[tk.Button] = None
        self.copy_button: Optional[tk.Button] = None
        self.transcription_text: Optional[tk.Text] = None
        self.record_button: Optional[tk.Button] = None

    def setup_ui(self, version: str) -> None:
        self.master.title(f'音声入力メモアプリ v{version}')

        self.record_button = tk.Button(
            self.master,
            text='音声入力開始',
            command=self._toggle_recording
        )
        self.record_button.pack(pady=10)

        self.transcription_text = tk.Text(
            self.master,
            height=int(self.config['UI']['TEXT_AREA_HEIGHT']),
            width=int(self.config['UI']['TEXT_AREA_WIDTH'])
        )
        self.transcription_text.pack(
            pady=int(self.config['UI']['TEXT_AREA_PADY'])
        )

        self.copy_button = tk.Button(
            self.master,
            text='クリップボードにコピー',
            command=self._copy_to_clipboard
        )
        self.copy_button.pack(pady=5)

        self.clear_button = tk.Button(
            self.master,
            text='テキストをクリア',
            command=self._clear_text
        )
        self.clear_button.pack(pady=5)

        self.comma_button = tk.Button(
            self.master,
            text=f'読点(、)あり:{self.config["KEYS"]["TOGGLE_COMMA"]}',
            command=self._toggle_comma
        )
        self.comma_button.pack(pady=5)

        self.punctuation_button = tk.Button(
            self.master,
            text=f'句点(。)あり:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}',
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
            text=f'句点(。){"あり" if use_punctuation else "なし"}:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}'
        )

    def update_comma_button(self, use_comma: bool) -> None:
        self.comma_button.config(
            text=f'読点(、){"あり" if use_comma else "なし"}:{self.config["KEYS"]["TOGGLE_COMMA"]}'
        )

    def append_transcription(self, text: str) -> None:
        current_text = self.transcription_text.get('1.0', tk.END).strip()
        if current_text:
            self.transcription_text.insert(tk.END, "\n")
        self.transcription_text.insert(tk.END, text)
        self.transcription_text.see(tk.END)

    def get_transcription_text(self) -> str:
        return self.transcription_text.get('1.0', tk.END).strip()

    def clear_transcription_text(self) -> None:
        self.transcription_text.delete('1.0', tk.END)
