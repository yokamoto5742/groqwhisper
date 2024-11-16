import os
import logging
import threading
import tkinter as tk
from typing import Optional, Dict, Any, Callable, List, Tuple
from functools import wraps

from service_audio_recorder import save_audio
from service_transcription import transcribe_audio
from service_text_processing import replace_text, copy_and_paste_transcription


def enhanced_safe_operation(method):
    """
    Enhanced safe operation decorator that properly propagates errors to the UI
    """

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            error_msg = f"{method.__name__}でエラーが発生しました: {str(e)}"
            logging.error(error_msg, exc_info=True)
            # メインスレッドで実行されていない場合、UIの更新を安全に行う
            if threading.current_thread() is not threading.main_thread():
                self.master.after(0, lambda: self._handle_error(error_msg))
            else:
                self._handle_error(error_msg)
            return None

    return wrapper


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
        self.processing_thread: Optional[threading.Thread] = None

        self.use_punctuation: bool = config['WHISPER'].getboolean('USE_PUNCTUATION', True)
        self.use_comma: bool = config['WHISPER'].getboolean('USE_COMMA', True)

    def _handle_error(self, error_msg: str) -> None:
        """エラーを統一的に処理するメソッド"""
        self.show_notification("エラー", error_msg)
        self.ui_callbacks['update_status_label'](
            f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
        )
        self.ui_callbacks['update_record_button'](False)
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    @enhanced_safe_operation
    def toggle_recording(self) -> None:
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    @enhanced_safe_operation
    def start_recording(self) -> None:
        if self.processing_thread and self.processing_thread.is_alive():
            raise RuntimeError("前回の処理が完了していません")

        self.recorder.start_recording()
        self.ui_callbacks['update_record_button'](True)
        self.ui_callbacks['update_status_label'](
            f"音声入力中... ({self.config['KEYS']['TOGGLE_RECORDING']}キーで停止)"
        )

        recording_thread = threading.Thread(target=self._safe_record, daemon=True)
        recording_thread.start()

        auto_stop_timer = int(self.config['RECORDING']['AUTO_STOP_TIMER'])
        self.recording_timer = threading.Timer(auto_stop_timer, self.auto_stop_recording)
        self.recording_timer.start()

        self.five_second_notification_shown = False
        self.five_second_timer = self.master.after(
            (auto_stop_timer - 5) * 1000,
            self.show_five_second_notification
        )

        logging.info("録音を開始しました")

    @enhanced_safe_operation
    def _safe_record(self) -> None:
        """録音処理を安全に実行するメソッド"""
        try:
            self.recorder.record()
        except Exception as e:
            self.master.after(0, lambda: self._handle_error(f"録音中にエラーが発生しました: {str(e)}"))
            self.stop_recording()

    @enhanced_safe_operation
    def stop_recording(self) -> None:
        try:
            if self.recording_timer and self.recording_timer.is_alive():
                self.recording_timer.cancel()
            if self.five_second_timer:
                self.master.after_cancel(self.five_second_timer)
                self.five_second_timer = None

            self._stop_recording_process()
        except Exception as e:
            self._handle_error(f"録音の停止中にエラーが発生しました: {str(e)}")

    @enhanced_safe_operation
    def auto_stop_recording(self) -> None:
        self.master.after(0, self._auto_stop_recording_ui)

    def _auto_stop_recording_ui(self) -> None:
        self.show_notification("自動停止", "音声入力を自動停止しました")
        self._stop_recording_process()

    @enhanced_safe_operation
    def _stop_recording_process(self) -> None:
        logging.info("録音停止プロセスを開始します")
        frames, sample_rate = self.recorder.stop_recording()
        logging.info(f"録音データを取得しました: フレーム数={len(frames)}, サンプルレート={sample_rate}")

        self.ui_callbacks['update_record_button'](False)
        self.ui_callbacks['update_status_label']("テキスト出力中...")

        self.processing_thread = threading.Thread(
            target=self._safe_process_audio,
            args=(frames, sample_rate),
            daemon=True
        )
        self.processing_thread.start()
        self.master.after(100, self._check_process_thread, self.processing_thread)
        logging.info("音声処理スレッドが開始されました")

    def _check_process_thread(self, thread: threading.Thread) -> None:
        """処理スレッドの状態を監視し、UIを適切に更新する"""
        if not thread.is_alive():
            self.ui_callbacks['update_status_label'](
                f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
            )
            self.processing_thread = None
            return

        self.ui_callbacks['update_status_label']("テキスト出力中...")
        self.master.after(100, self._check_process_thread, thread)

    @enhanced_safe_operation
    def show_five_second_notification(self) -> None:
        if self.recorder.is_recording and not self.five_second_notification_shown:
            self.master.lift()
            self.master.attributes('-topmost', True)
            self.master.attributes('-topmost', False)
            self.show_notification("自動停止", "あと5秒で音声入力を停止します")
            self.five_second_notification_shown = True

    @enhanced_safe_operation
    def _safe_process_audio(self, frames: List[bytes], sample_rate: int) -> None:
        """音声処理を安全に実行し、エラーを適切に処理するメソッド"""
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
            if not replaced_transcription:
                raise ValueError("テキスト置換に失敗しました")

            self.master.after(0, lambda: self._safe_ui_update(replaced_transcription))

        finally:
            if temp_audio_file and os.path.exists(temp_audio_file):
                try:
                    os.unlink(temp_audio_file)
                except OSError as e:
                    logging.error(f"一時ファイルの削除中にエラーが発生しました: {str(e)}", exc_info=True)

    @enhanced_safe_operation
    def _safe_ui_update(self, text: str) -> None:
        """UIの更新を安全に実行するメソッド"""
        if not text:
            return

        self.ui_callbacks['append_transcription'](text)
        paste_delay = int(float(self.config['CLIPBOARD'].get('PASTE_DELAY', 0.5)) * 1000)
        self.master.after(paste_delay, lambda: self._safe_copy_and_paste(text))

    @enhanced_safe_operation
    def _safe_copy_and_paste(self, text: str) -> None:
        """コピー&ペースト操作を安全に実行するメソッド"""
        copy_and_paste_transcription(text, self.replacements, self.config)

    def cleanup(self) -> None:
        """アプリケーション終了時のクリーンアップ処理"""
        if self.recording_timer and self.recording_timer.is_alive():
            self.recording_timer.cancel()
        if self.five_second_timer:
            self.master.after_cancel(self.five_second_timer)
            self.five_second_timer = None
        if self.paste_timer:
            self.paste_timer.cancel()
        if self.processing_thread and self.processing_thread.is_alive():
            # スレッドの強制終了は避けるべきだが、アプリケーション終了時は例外
            self.processing_thread = None
