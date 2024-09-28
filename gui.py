import threading
import tkinter as tk
import keyboard
from text_processing import copy_and_paste_transcription, replace_text
from transcription import transcribe_audio


class AudioRecorderGUI:
    def __init__(self, master, config, recorder, client, replacements, version, last_updated):
        self.master = master
        self.config = config
        self.recorder = recorder
        self.client = client
        self.replacements = replacements
        self.version = version
        self.last_updated = last_updated

        self.recording_timer = None
        self.five_second_timer = None
        self.five_second_notification_shown = False
        self.use_punctuation = config['WHISPER'].getboolean('USE_PUNCTUATION', True)
        self.use_comma = config['WHISPER'].getboolean('USE_COMMA', True)

        self.setup_ui()
        self.setup_keyboard_listeners()

    def setup_ui(self):
        self.master.title(f'音声入力メモアプリ v{self.version}')

        self.record_button = tk.Button(self.master, text='音声入力開始', command=self.toggle_recording)
        self.record_button.pack(pady=10)

        self.transcription_text = tk.Text(self.master, height=int(self.config['UI']['TEXT_AREA_HEIGHT']),
                                          width=int(self.config['UI']['TEXT_AREA_WIDTH']))
        self.transcription_text.pack(pady=int(self.config['UI']['TEXT_AREA_PADY']))

        self.copy_button = tk.Button(self.master, text='クリップボードにコピー', command=self.copy_to_clipboard)
        self.copy_button.pack(pady=5)

        self.clear_button = tk.Button(self.master, text='テキストをクリア', command=self.clear_text)
        self.clear_button.pack(pady=5)

        self.comma_button = tk.Button(self.master,
                                      text=f'読点(、)あり:{self.config["KEYS"]["TOGGLE_COMMA"]}' if self.use_comma else f'読点(、)なし:{self.config["KEYS"]["TOGGLE_COMMA"]}',
                                      command=self.toggle_comma)
        self.comma_button.pack(pady=5)

        self.punctuation_button = tk.Button(self.master,
                                            text=f'句点(。)あり:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}' if self.use_punctuation else f'句点(。)なし:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}',
                                            command=self.toggle_punctuation)
        self.punctuation_button.pack(pady=5)

        self.status_label = tk.Label(self.master,
                                     text=f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止 {self.config['KEYS']['EXIT_APP']}キーで終了")
        self.status_label.pack(pady=5)

    def setup_keyboard_listeners(self):
        keyboard.on_press_key(self.config['KEYS']['TOGGLE_RECORDING'], self.on_toggle_key)
        keyboard.on_press_key(self.config['KEYS']['EXIT_APP'], self.on_exit_key)
        keyboard.on_press_key(self.config['KEYS']['TOGGLE_PUNCTUATION'], self.on_toggle_punctuation_key)
        keyboard.on_press_key(self.config['KEYS']['TOGGLE_COMMA'], self.on_toggle_comma_key)

    def toggle_punctuation(self):
        self.use_punctuation = not self.use_punctuation
        self.punctuation_button.config(
            text=f'句点(。)あり:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}' if self.use_punctuation else f'句点(。)なし:{self.config["KEYS"]["TOGGLE_PUNCTUATION"]}')
        print(f"句点(。)モード: {'あり' if self.use_punctuation else 'なし'}")
        self.config['WHISPER']['USE_PUNCTUATION'] = str(self.use_punctuation)
        self.save_config()

    def toggle_comma(self):
        self.use_comma = not self.use_comma
        self.comma_button.config(
            text=f'読点(、)あり:{self.config["KEYS"]["TOGGLE_COMMA"]}' if self.use_comma else f'読点(、)なし:{self.config["KEYS"]["TOGGLE_COMMA"]}')
        print(f"読点(、)モード: {'あり' if self.use_comma else 'なし'}")
        self.config['WHISPER']['USE_COMMA'] = str(self.use_comma)
        self.save_config()

    def on_toggle_punctuation_key(self, e):
        self.master.after(0, self.toggle_punctuation)

    def on_toggle_comma_key(self, e):
        self.master.after(0, self.toggle_comma)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        try:
            self.recorder.start_recording()
            self.record_button.config(text='音声入力停止')
            self.status_label.config(text=f"音声入力中... ({self.config['KEYS']['TOGGLE_RECORDING']}キーで停止)")
            threading.Thread(target=self.recorder.record, daemon=True).start()

            auto_stop_timer = int(self.config['RECORDING']['AUTO_STOP_TIMER'])
            self.recording_timer = threading.Timer(auto_stop_timer, self.auto_stop_recording)
            self.recording_timer.start()

            self.five_second_notification_shown = False
            self.five_second_timer = self.master.after((auto_stop_timer - 5) * 1000, self.show_five_second_notification)
        except Exception as e:
            print(f"音声入力の開始中にエラーが発生しました: {str(e)}")
            self.record_button.config(text='音声入力開始')

    def stop_recording(self):
        if self.recording_timer and self.recording_timer.is_alive():
            self.recording_timer.cancel()
        if self.five_second_timer:
            self.master.after_cancel(self.five_second_timer)
            self.five_second_timer = None
        self._stop_recording_process()

    def auto_stop_recording(self):
        self.master.after(0, self._auto_stop_recording_ui)

    def _auto_stop_recording_ui(self):
        self.show_timed_message("自動停止", "音声入力を自動停止しました")
        self._stop_recording_process()

    def _stop_recording_process(self):
        try:
            frames, sample_rate = self.recorder.stop_recording()
            self.record_button.config(text='音声入力開始')
            self.status_label.config(text="テキスト出力中...")
            threading.Thread(target=self.process_audio, args=(frames, sample_rate), daemon=True).start()
        except Exception as e:
            print(f"音声入力の停止中にエラーが発生しました: {str(e)}")

    def show_five_second_notification(self):
        if self.recorder.is_recording and not self.five_second_notification_shown:
            self.master.lift()
            self.master.attributes('-topmost', True)
            self.master.attributes('-topmost', False)
            self.show_timed_message("自動停止", "あと5秒で音声入力を停止します")
            self.five_second_notification_shown = True

    def show_timed_message(self, title, message, duration=2000):
        popup = tk.Toplevel(self.master)
        popup.title(title)
        label = tk.Label(popup, text=message)
        label.pack(padx=20, pady=20)
        popup.after(duration, popup.destroy)

    def process_audio(self, frames, sample_rate):
        from audio_recorder import save_audio  # Avoid circular import
        temp_audio_file = save_audio(frames, sample_rate, self.config)
        if temp_audio_file:
            transcription = transcribe_audio(temp_audio_file, self.use_punctuation, self.use_comma, self.config,
                                             self.client)
            if transcription:
                replaced_transcription = replace_text(transcription, self.replacements)
                self.master.after(0, self.append_transcription, replaced_transcription)
                copy_and_paste_transcription(replaced_transcription, self.replacements, self.config)
            try:
                import os
                os.unlink(temp_audio_file)
            except Exception as e:
                print(f"一時ファイルの削除中にエラーが発生しました: {str(e)}")
        self.status_label.config(
            text=f"{self.config['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止 {self.config['KEYS']['EXIT_APP']}キーで終了")

    def append_transcription(self, text):
        current_text = self.transcription_text.get('1.0', tk.END).strip()
        if current_text:
            self.transcription_text.insert(tk.END, "\n")
        self.transcription_text.insert(tk.END, text)
        self.transcription_text.see(tk.END)

    def copy_to_clipboard(self):
        text = self.transcription_text.get('1.0', tk.END).strip()
        copy_and_paste_transcription(text, self.replacements, self.config)
        print("テキストをクリップボードにコピーし、貼り付けました。")

    def clear_text(self):
        self.transcription_text.delete('1.0', tk.END)
        print("テキストをクリアしました。")

    def on_toggle_key(self, e):
        self.master.after(0, self.toggle_recording)

    def on_exit_key(self, e):
        self.master.after(0, self.close_application)

    def close_application(self):
        if self.recorder.is_recording:
            self.stop_recording()
        if self.recording_timer and self.recording_timer.is_alive():
            self.recording_timer.cancel()
        self.master.quit()

    def save_config(self):
        from config import save_config  # Avoid circular import
        save_config(self.config)
