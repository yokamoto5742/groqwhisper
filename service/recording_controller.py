import glob
import logging
import os
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List

from audio_recorder import save_audio
from text_processing import copy_and_paste_transcription
from transcription import transcribe_audio


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
        self.cancel_processing = None
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
        self.use_comma: bool = self.use_punctuation

        self.temp_dir = config['PATHS']['TEMP_DIR']
        self.cleanup_minutes = int(config['PATHS']['CLEANUP_MINUTES'])
        os.makedirs(self.temp_dir, exist_ok=True)
        self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        try:
            current_time = datetime.now()
            pattern = os.path.join(self.temp_dir, "*.wav")

            for file_path in glob.glob(pattern):
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                if current_time - file_modified > timedelta(minutes=self.cleanup_minutes):
                    try:
                        os.remove(file_path)
                        logging.info(f"古い一時ファイルを削除しました: {file_path}")
                    except Exception as e:
                        logging.error(f"ファイル削除中にエラーが発生しました: {file_path}, {e}")
        except Exception as e:
            logging.error(f"クリーンアップ処理中にエラーが発生しました: {e}")

    def _handle_error(self, error_msg: str):
        self.show_notification("エラー", error_msg)
        self.ui_callbacks['update_status_label'](
            f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
        )
        self.ui_callbacks['update_record_button'](False)
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if self.processing_thread and self.processing_thread.is_alive():
            raise RuntimeError("前回の処理が完了していません")

        self.recorder.start_recording()
        self.ui_callbacks['update_record_button'](True)
        self.ui_callbacks['update_status_label'](
            f"音声入力中... ({self.config['KEYS']['TOGGLE_RECORDING']}キーで停止)"
        )

        recording_thread = threading.Thread(target=self._safe_record, daemon=False)
        recording_thread.start()

        auto_stop_timer = int(self.config['RECORDING']['AUTO_STOP_TIMER'])
        self.recording_timer = threading.Timer(auto_stop_timer, self.auto_stop_recording)
        self.recording_timer.start()

        self.five_second_notification_shown = False
        self.five_second_timer = self.master.after(
            (auto_stop_timer - 5) * 1000,
            self.show_five_second_notification
        )

    def _safe_record(self):
        self.recorder.record()

    def stop_recording(self):
        try:
            if self.recording_timer and self.recording_timer.is_alive():
                self.recording_timer.cancel()
            if self.five_second_timer:
                self.master.after_cancel(self.five_second_timer)
                self.five_second_timer = None

            self._stop_recording_process()
        except Exception as e:
            self._handle_error(f"録音の停止中にエラーが発生しました: {str(e)}")

    def auto_stop_recording(self):
        self.master.after(0, self._auto_stop_recording_ui)

    def _auto_stop_recording_ui(self):
        self.show_notification("自動停止", "アプリケーションを終了します")
        self._stop_recording_process()
        self.master.after(1000, self.master.quit)

    def _stop_recording_process(self):
        frames, sample_rate = self.recorder.stop_recording()
        logging.info(f"録音データを取得しました")

        self.ui_callbacks['update_record_button'](False)
        self.ui_callbacks['update_status_label']("テキスト出力中...")

        self.processing_thread = threading.Thread(
            target=self.transcribe_audio_frames,
            args=(frames, sample_rate),
            daemon=False
        )
        self.processing_thread.start()
        self.master.after(100, self._check_process_thread, self.processing_thread)

    def _check_process_thread(self, thread: threading.Thread):
        if not thread.is_alive():
            self.ui_callbacks['update_status_label'](
                f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
            )
            self.processing_thread = None
            return

        self.ui_callbacks['update_status_label']("テキスト出力中...")
        self.master.after(100, self._check_process_thread, thread)

    def show_five_second_notification(self):
        if self.recorder.is_recording and not self.five_second_notification_shown:
            self.master.lift()
            self.master.attributes('-topmost', True)
            self.master.attributes('-topmost', False)
            self.show_notification("自動停止", "あと5秒で音声入力を停止します")
            self.five_second_notification_shown = True

    def handle_audio_file(self, event):
        file_path = self.master.clipboard_get()
        if not os.path.exists(file_path):
            self.show_notification('エラー', '音声ファイルが見つかりません')
            return

        self.ui_callbacks['update_status_label']('音声ファイル処理中...')
        try:
            transcription = transcribe_audio(
                file_path,
                self.use_punctuation,
                self.use_comma,
                self.config,
                self.client
            )
            if transcription:
                self.ui_update(transcription)
            else:
                raise ValueError('音声ファイルの処理に失敗しました')
        except Exception as e:
            self.show_notification('エラー', str(e))
        finally:
            self.ui_callbacks['update_status_label'](
                f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
            )

    def transcribe_audio_frames(self, frames: List[bytes], sample_rate: int):
        try:
            temp_audio_file = save_audio(frames, sample_rate, self.config)
            if not temp_audio_file:
                raise ValueError("音声ファイルの保存に失敗しました")

            if hasattr(self, 'cancel_processing') and self.cancel_processing:
                logging.info("処理がキャンセルされました")
                return

            transcription = transcribe_audio(
                temp_audio_file,
                self.use_punctuation,
                self.use_comma,
                self.config,
                self.client
            )

            if not transcription:
                raise ValueError("音声ファイルの文字起こしに失敗しました")

            if hasattr(self, 'cancel_processing') and self.cancel_processing:
                return

            self.master.after(0, lambda: self.ui_update(transcription))

        except Exception as e:
            logging.error(f"文字起こし処理中にエラーが発生: {str(e)}")
            self.master.after(0, lambda: self._handle_error(str(e)))

    def ui_update(self, text: str):
        paste_delay = int(float(self.config['CLIPBOARD'].get('PASTE_DELAY', 0.1)) * 1000)
        self.master.after(paste_delay, lambda: self.copy_and_paste(text))

    def copy_and_paste(self, text: str):
        copy_and_paste_transcription(text, self.replacements, self.config)

    def cleanup(self):
        try:
            if self.recorder.is_recording:
                self.stop_recording()

            if self.processing_thread and self.processing_thread.is_alive():
                for _ in range(100):  # 10秒間待機
                    if not self.processing_thread.is_alive():
                        break
                    time.sleep(0.1)

                if self.processing_thread.is_alive():
                    logging.warning("処理スレッドが強制終了されました")
                    self.cancel_processing = True
                    self.processing_thread.join(1.0)

            if self.recording_timer and self.recording_timer.is_alive():
                self.recording_timer.cancel()

            if self.five_second_timer:
                self.master.after_cancel(self.five_second_timer)

            self._cleanup_temp_files()

        except Exception as e:
            logging.error(f"クリーンアップ処理中にエラーが発生しました: {str(e)}")

    def _wait_for_processing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            logging.info("処理スレッドの完了を待機中...")
            self.ui_callbacks['update_status_label']("処理完了待機中...")
            self.processing_thread.join(timeout=5.0)

            if self.processing_thread.is_alive():
                logging.warning("処理スレッドの待機がタイムアウトしました")
            else:
                logging.info("処理スレッドの待機が完了しました")
