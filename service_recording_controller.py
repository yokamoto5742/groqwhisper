import os
import logging
import threading
import tkinter as tk
from typing import Optional, Dict, Any, Callable, List, Tuple

from service_audio_recorder import save_audio
from service_transcription import transcribe_audio
from service_text_processing import replace_text, safe_operation, copy_and_paste_transcription


class RecordingController:
    def __init__(
            self,
            master: tk.Tk,
            config: Dict[str, Any],
            recorder: Any,
            client: Any,
            replacements: Dict[str, str],
            ui_callbacks: Dict[str, Callable],
            notification_callback: Callable
    ):
        self.master = master
        self.config = config
        self.recorder = recorder
        self.client = client
        self.replacements = replacements
        self.ui_callbacks = ui_callbacks
        self.show_notification = notification_callback

        self.recording_timer: Optional[threading.Timer] = None
        self.five_second_timer: Optional[str] = None
        self.paste_timer = None
        self.five_second_notification_shown: bool = False

        self.use_punctuation: bool = config['WHISPER'].getboolean('USE_PUNCTUATION', True)
        self.use_comma: bool = config['WHISPER'].getboolean('USE_COMMA', True)

    def toggle_recording(self) -> None:
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self) -> None:
        try:
            self.recorder.start_recording()

            self.ui_callbacks['update_record_button'](True)
            self.ui_callbacks['update_status_label'](
                f"音声入力中... ({self.config['KEYS']['TOGGLE_RECORDING']}キーで停止)"
            )

            threading.Thread(target=self.recorder.record, daemon=True).start()

            auto_stop_timer = int(self.config['RECORDING']['AUTO_STOP_TIMER'])
            self.recording_timer = threading.Timer(auto_stop_timer, self.auto_stop_recording)
            self.recording_timer.start()

            self.five_second_notification_shown = False
            self.five_second_timer = self.master.after(
                (auto_stop_timer - 5) * 1000,
                self.show_five_second_notification
            )

            logging.info("録音を開始しました")

        except Exception as e:
            logging.error(f"録音の開始中にエラーが発生しました: {str(e)}", exc_info=True)
            self.ui_callbacks['update_record_button'](False)
            self.show_notification("エラー", "録音の開始に失敗しました")

    def stop_recording(self) -> None:
        if self.recording_timer and self.recording_timer.is_alive():
            self.recording_timer.cancel()
        if self.five_second_timer:
            self.master.after_cancel(self.five_second_timer)
            self.five_second_timer = None
        self._stop_recording_process()

    def auto_stop_recording(self) -> None:
        self.master.after(0, self._auto_stop_recording_ui)

    def _auto_stop_recording_ui(self) -> None:
        self.show_notification("自動停止", "音声入力を自動停止しました")
        self._stop_recording_process()

    def _stop_recording_process(self) -> None:
        try:
            logging.info("録音停止プロセスを開始します")
            frames, sample_rate = self.recorder.stop_recording()
            logging.info(f"録音データを取得しました: フレーム数={len(frames)}, サンプルレート={sample_rate}")

            self.ui_callbacks['update_record_button'](False)
            self.ui_callbacks['update_status_label']("テキスト出力中...")

            process_thread = threading.Thread(
                target=self.process_audio,
                args=(frames, sample_rate),
                daemon=True
            )
            process_thread.start()
            logging.info("音声処理スレッドが開始されました")

        except Exception as e:
            logging.error(f"録音の停止中にエラーが発生しました: {str(e)}")
            logging.error(f"詳細なエラー情報: {threading.format_exc()}")
            self.ui_callbacks['update_record_button'](False)
            self.ui_callbacks['update_status_label'](
                f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
            )

    def show_five_second_notification(self) -> None:
        if self.recorder.is_recording and not self.five_second_notification_shown:
            self.master.lift()
            self.master.attributes('-topmost', True)
            self.master.attributes('-topmost', False)
            self.show_notification("自動停止", "あと5秒で音声入力を停止します")
            self.five_second_notification_shown = True

    @safe_operation
    def process_audio(self, frames: List[bytes], sample_rate: int) -> None:
        temp_audio_file = None
        try:
            temp_audio_file = save_audio(frames, sample_rate, self.config)
            if not temp_audio_file:
                raise ValueError("音声ファイルの保存に失敗しました")

            transcription = transcribe_audio(
                temp_audio_file,
                self.use_punctuation,
                self.use_comma,
                self.config,
                self.client
            )
            if not transcription:
                raise ValueError("文字起こしに失敗しました")

            replaced_transcription = replace_text(transcription, self.replacements)

            self.master.after(0, lambda: self._safe_ui_update(replaced_transcription))

        except Exception as e:
            error_message = f"音声処理中にエラーが発生しました: {str(e)}"
            logging.error(error_message, exc_info=True)
            self.master.after(0, lambda: self.show_notification("エラー", error_message))

        finally:
            if temp_audio_file and os.path.exists(temp_audio_file):
                try:
                    os.unlink(temp_audio_file)
                except OSError as e:
                    logging.error(f"一時ファイルの削除中にエラーが発生しました: {str(e)}", exc_info=True)

            self.master.after(0, self.update_status_label)

    def _safe_ui_update(self, text: str) -> None:
        if not text:
            return

        try:
            self.ui_callbacks['append_transcription'](text)
            paste_delay = float(self.config['CLIPBOARD'].get('PASTE_DELAY', 0.5))
            self.master.after(int(paste_delay * 1000), lambda: self.safe_copy_and_paste(text))

        except Exception as e:
            error_message = f"UI更新エラー: {str(e)}"
            logging.error(error_message, exc_info=True)
            self.show_notification("エラー", "テキスト処理中にエラーが発生しました")

    def update_status_label(self) -> None:
        self.ui_callbacks['update_status_label'](
            f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止 "
            f"{self.config['KEYS']['EXIT_APP']}キーで終了"
        )

    @safe_operation
    def safe_copy_and_paste(self, text: str) -> None:
        copy_and_paste_transcription(text, self.replacements, self.config)

    def cleanup(self) -> None:
        if self.recording_timer and self.recording_timer.is_alive():
            self.recording_timer.cancel()
        if self.five_second_timer:
            self.master.after_cancel(self.five_second_timer)
            self.five_second_timer = None
        if self.paste_timer:
            self.paste_timer.cancel()
