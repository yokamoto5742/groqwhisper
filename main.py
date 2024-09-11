import os
import tempfile
import wave
import pyaudio
import pyperclip
import tkinter as tk
import threading
import keyboard
import pyautogui
from groq import Groq
import configparser

VERSION = "0.0.1"
LAST_UPDATED = "2024/09/11"

# 設定ファイルの読み込み
config = configparser.ConfigParser()
with open('config.ini', 'r', encoding='utf-8') as f:
    config.read_file(f)

replacements = dict(config['REPLACEMENTS'])
start_minimized = config['OPTIONS'].getboolean('start_minimized', True)
TOGGLE_RECORDING_KEY = config['KEYS']['TOGGLE_RECORDING']
EXIT_APP_KEY = config['KEYS']['EXIT_APP']

# Groqクライアントのセットアップ
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def replace_text(text, replacements):
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


class AudioRecorder:
    def __init__(self):
        self.sample_rate = int(config['AUDIO']['SAMPLE_RATE'])
        self.channels = int(config['AUDIO']['CHANNELS'])
        self.chunk = int(config['AUDIO']['CHUNK'])
        self.frames = []
        self.is_recording = False
        self.p = None
        self.stream = None

    def start_recording(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk,
        )
        self.is_recording = True
        self.frames = []
        print("録音開始...")

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
        print("録音終了.")
        return self.frames, self.sample_rate

    def record(self):
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
            except Exception as e:
                print(f"録音中にエラーが発生しました: {str(e)}")
                self.is_recording = False
                break


def save_audio(frames, sample_rate):
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            wf = wave.open(temp_audio.name, "wb")
            wf.setnchannels(int(config['AUDIO']['CHANNELS']))
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(frames))
            wf.close()
            return temp_audio.name
    except Exception as e:
        print(f"音声ファイルの保存中にエラーが発生しました: {str(e)}")
        return None


def transcribe_audio(audio_file_path):
    if not audio_file_path:
        return None
    try:
        with open(audio_file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file.read()),
                model=config['WHISPER']['MODEL'],
                prompt=config['WHISPER']['PROMPT'],
                response_format="text",
                language=config['WHISPER']['LANGUAGE'],
            )
        return transcription
    except Exception as e:
        print(f"文字起こし中にエラーが発生しました: {str(e)}")
        return None


def copy_and_paste_transcription(text):
    if text:
        replaced_text = replace_text(text, replacements)
        pyperclip.copy(replaced_text)
        # config.iniから待機時間を読み込む
        paste_delay = float(config['CLIPBOARD']['PASTE_DELAY'])
        # 設定された待機時間後にCtrl+Vを実行
        threading.Timer(paste_delay, lambda: pyautogui.hotkey('ctrl', 'v')).start()


class AudioRecorderGUI:
    def __init__(self, master):
        self.master = master
        master.title('眼科医師用音声録音・文字起こしアプリ')

        self.recorder = AudioRecorder()

        self.record_button = tk.Button(master, text='録音開始', command=self.toggle_recording)
        self.record_button.pack(pady=10)

        self.transcription_text = tk.Text(master, height=10, width=50)
        self.transcription_text.pack(pady=10)

        self.copy_button = tk.Button(master, text='クリップボードにコピー', command=self.copy_to_clipboard)
        self.copy_button.pack(pady=5)

        self.clear_button = tk.Button(master, text='テキストをクリア', command=self.clear_text)
        self.clear_button.pack(pady=5)

        self.status_label = tk.Label(master, text=f"{TOGGLE_RECORDING_KEY}キーで録音開始/停止、{EXIT_APP_KEY}キーで終了")
        self.status_label.pack(pady=5)

        keyboard.on_press_key(TOGGLE_RECORDING_KEY, self.on_toggle_key)
        keyboard.on_press_key(EXIT_APP_KEY, self.on_exit_key)

        if start_minimized:
            self.master.iconify()

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        try:
            self.recorder.start_recording()
            self.record_button.config(text='録音停止')
            self.status_label.config(text=f"録音中... ({TOGGLE_RECORDING_KEY}キーで停止)")
            threading.Thread(target=self.recorder.record, daemon=True).start()
        except Exception as e:
            print(f"録音の開始中にエラーが発生しました: {str(e)}")
            self.record_button.config(text='録音開始')

    def stop_recording(self):
        try:
            frames, sample_rate = self.recorder.stop_recording()
            self.record_button.config(text='録音開始')
            self.status_label.config(text="文字起こし中...")
            threading.Thread(target=self.process_audio, args=(frames, sample_rate), daemon=True).start()
        except Exception as e:
            print(f"録音の停止中にエラーが発生しました: {str(e)}")

    def process_audio(self, frames, sample_rate):
        temp_audio_file = save_audio(frames, sample_rate)
        if temp_audio_file:
            transcription = transcribe_audio(temp_audio_file)
            if transcription:
                replaced_transcription = replace_text(transcription, replacements)
                self.master.after(0, self.append_transcription, replaced_transcription)
                copy_and_paste_transcription(replaced_transcription)
            try:
                os.unlink(temp_audio_file)
            except Exception as e:
                print(f"一時ファイルの削除中にエラーが発生しました: {str(e)}")
        self.status_label.config(text=f"{TOGGLE_RECORDING_KEY}キーで録音開始/停止")

    def append_transcription(self, text):
        current_text = self.transcription_text.get('1.0', tk.END).strip()
        if current_text:
            self.transcription_text.insert(tk.END, "")
        self.transcription_text.insert(tk.END, text)
        self.transcription_text.see(tk.END)

    def copy_to_clipboard(self):
        text = self.transcription_text.get('1.0', tk.END).strip()
        copy_and_paste_transcription(text)
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
        self.master.quit()


def main():
    root = tk.Tk()
    app = AudioRecorderGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close_application)
    root.mainloop()


if __name__ == "__main__":
    main()
