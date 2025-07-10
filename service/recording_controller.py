import glob
import logging
import os
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from external_service.groq_api import transcribe_audio
from service.audio_recorder import save_audio
from service.text_processing import copy_and_paste_transcription
from utils.config_manager import get_config_value


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
        self.cancel_processing = False
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

        self._ui_lock = threading.Lock()
        self._scheduled_tasks = set()

        self.use_punctuation: bool = get_config_value(config, 'WHISPER', 'USE_PUNCTUATION', True)
        self.use_comma: bool = self.use_punctuation

        self.temp_dir = config['PATHS']['TEMP_DIR']
        self.cleanup_minutes = int(config['PATHS']['CLEANUP_MINUTES'])

        os.makedirs(self.temp_dir, exist_ok=True)
        self._cleanup_temp_files()

    def _is_ui_valid(self) -> bool:
        try:
            return (self.master is not None and
                    hasattr(self.master, 'winfo_exists') and
                    self.master.winfo_exists())
        except tk.TclError:
            return False
        except Exception:
            return False

    def _schedule_ui_task(self, delay: int, callback: Callable, *args) -> Optional[str]:
        if not self._is_ui_valid():
            logging.warning("UIが無効でタスクをスケジュールできません")
            return None

        try:
            task_id = self.master.after(delay, self._safe_ui_task_wrapper, callback, *args)
            with self._ui_lock:
                self._scheduled_tasks.add(task_id)
            return task_id
        except Exception as e:
            logging.error(f"UIタスクのスケジュール中にエラー: {str(e)}")
            return None

    def _safe_ui_task_wrapper(self, callback: Callable, *args):
        task_id = None
        try:
            with self._ui_lock:
                self._scheduled_tasks.clear()

            if self._is_ui_valid():
                callback(*args)
            else:
                logging.warning("UIが無効でタスクを実行できません")
        except Exception as e:
            logging.error(f"UIタスク実行中にエラー: {str(e)}")

    def _cancel_scheduled_tasks(self):
        with self._ui_lock:
            for task_id in self._scheduled_tasks:
                try:
                    if self._is_ui_valid():
                        self.master.after_cancel(task_id)
                except Exception as e:
                    logging.debug(f"タスクキャンセル中にエラー: {str(e)}")
            self._scheduled_tasks.clear()

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
        try:
            if self._is_ui_valid():
                self.show_notification("エラー", error_msg)
                self.ui_callbacks['update_status_label'](
                    f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
                )
                self.ui_callbacks['update_record_button'](False)
                if self.recorder.is_recording:
                    self.recorder.stop_recording()
        except Exception as e:
            logging.error(f"エラーハンドリング中にエラー: {str(e)}")

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if self.processing_thread and self.processing_thread.is_alive():
            raise RuntimeError("前回の処理が完了していません")

        self.cancel_processing = False
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
        self.five_second_timer = self._schedule_ui_task(
            (auto_stop_timer - 5) * 1000,
            self.show_five_second_notification
        )

    def _safe_record(self):
        try:
            self.recorder.record()
        except Exception as e:
            logging.error(f"録音中にエラーが発生しました: {str(e)}")
            self._schedule_ui_task(0, self._safe_error_handler, f"録音中にエラーが発生しました: {str(e)}")

    def stop_recording(self):
        try:
            if self.recording_timer and self.recording_timer.is_alive():
                self.recording_timer.cancel()

            if self.five_second_timer:
                try:
                    if self._is_ui_valid():
                        self.master.after_cancel(self.five_second_timer)
                except Exception:
                    pass  # 既にキャンセルされている可能性があるため無視
                self.five_second_timer = None

            self._stop_recording_process()
        except Exception as e:
            self._safe_error_handler(f"録音の停止中にエラーが発生しました: {str(e)}")

    def auto_stop_recording(self):
        self._schedule_ui_task(0, self._auto_stop_recording_ui)

    def _auto_stop_recording_ui(self):
        try:
            self.show_notification("自動停止", "アプリケーションを終了します")
            self._stop_recording_process()
            self._schedule_ui_task(1000, self.master.quit)
        except Exception as e:
            logging.error(f"自動停止処理中にエラー: {str(e)}")

    def _stop_recording_process(self):
        try:
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

            self._schedule_ui_task(100, self._check_process_thread, self.processing_thread)
        except Exception as e:
            logging.error(f"録音停止処理中にエラー: {str(e)}")
            self._safe_error_handler(f"録音停止処理中にエラー: {str(e)}")

    def _check_process_thread(self, thread: threading.Thread):
        try:
            if not thread.is_alive():
                self.ui_callbacks['update_status_label'](
                    f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"
                )
                self.processing_thread = None
                return

            self.ui_callbacks['update_status_label']("テキスト出力中...")
            self._schedule_ui_task(100, self._check_process_thread, thread)
        except Exception as e:
            logging.error(f"処理スレッドチェック中にエラー: {str(e)}")

    def show_five_second_notification(self):
        try:
            if self.recorder.is_recording and not self.five_second_notification_shown:
                if self._is_ui_valid():
                    self.master.lift()
                    self.master.attributes('-topmost', True)
                    self.master.attributes('-topmost', False)
                    self.show_notification("自動停止", "あと5秒で音声入力を停止します")
                    self.five_second_notification_shown = True
        except Exception as e:
            logging.error(f"通知表示中にエラー: {str(e)}")

    def handle_audio_file(self, event):
        try:
            file_path = self.master.clipboard_get()
            if not os.path.exists(file_path):
                self.show_notification('エラー', '音声ファイルが見つかりません')
                return

            self.ui_callbacks['update_status_label']('音声ファイル処理中...')

            transcription = transcribe_audio(
                file_path,
                self.use_punctuation,
                self.use_comma,
                self.config,
                self.client
            )
            if transcription:
                self._safe_ui_update(transcription)
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
            logging.info("音声フレーム処理開始")

            if self.cancel_processing:
                logging.info("処理がキャンセルされました")
                return

            temp_audio_file = save_audio(frames, sample_rate, self.config)
            if not temp_audio_file:
                raise ValueError("音声ファイルの保存に失敗しました")

            if self.cancel_processing:
                logging.info("処理がキャンセルされました")
                return

            logging.info("文字起こし開始")
            transcription = transcribe_audio(
                temp_audio_file,
                self.use_punctuation,
                self.use_comma,
                self.config,
                self.client
            )

            if not transcription:
                raise ValueError("音声ファイルの文字起こしに失敗しました")

            if self.cancel_processing:
                logging.info("処理がキャンセルされました")
                return

            self._schedule_ui_task(0, self._safe_ui_update, transcription)

        except Exception as e:
            logging.error(f"文字起こし処理中にエラー: {str(e)}")
            self._schedule_ui_task(0, self._safe_error_handler, str(e))

    def _safe_ui_update(self, text: str):
        try:
            if self._is_ui_valid():
                self.ui_update(text)
            else:
                logging.warning("UIが無効なため、UI更新をスキップします")
        except Exception as e:
            logging.error(f"UI更新中にエラー: {str(e)}")

    def _safe_error_handler(self, error_msg: str):
        try:
            if self._is_ui_valid():
                self._handle_error(error_msg)
            else:
                logging.error(f"UI無効時のエラー: {error_msg}")
        except Exception as e:
            logging.error(f"エラーハンドリング中にエラー: {str(e)}")

    def ui_update(self, text: str):
        try:
            paste_delay = int(float(self.config['CLIPBOARD'].get('PASTE_DELAY', 0.1)) * 1000)
            self._schedule_ui_task(paste_delay, self.copy_and_paste, text)
        except Exception as e:
            logging.error(f"UI更新中にエラー: {str(e)}")

    def copy_and_paste(self, text: str):
        try:
            threading.Thread(
                target=self._safe_copy_and_paste,
                args=(text,),
                daemon=True
            ).start()
        except Exception as e:
            logging.error(f"コピー&ペースト開始中にエラー: {str(e)}")

    def _safe_copy_and_paste(self, text: str):
        try:
            copy_and_paste_transcription(text, self.replacements, self.config)
        except Exception as e:
            logging.error(f"コピー&ペースト実行中にエラー: {str(e)}")
            self._schedule_ui_task(0, self._safe_error_handler, f"コピー&ペースト中にエラー: {str(e)}")

    def cleanup(self):
        try:
            self.cancel_processing = True
            self._cancel_scheduled_tasks()

            if self.recorder.is_recording:
                self.stop_recording()

            if self.processing_thread and self.processing_thread.is_alive():
                logging.info("処理スレッドの完了を待機中...")
                for _ in range(50):  # 5秒間待機
                    if not self.processing_thread.is_alive():
                        break
                    time.sleep(0.1)

                if self.processing_thread.is_alive():
                    logging.warning("処理スレッドが強制終了されました")
                    self.processing_thread.join(1.0)

            if self.recording_timer and self.recording_timer.is_alive():
                self.recording_timer.cancel()

            if self.five_second_timer:
                try:
                    if self._is_ui_valid():
                        self.master.after_cancel(self.five_second_timer)
                except Exception:
                    pass

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
