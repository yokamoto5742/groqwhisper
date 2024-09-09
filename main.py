import os
import tempfile
import wave
import pyaudio
import pyperclip
import tkinter as tk
import threading
import keyboard
from groq import Groq

VERSION = "0.2.0"
LAST_UPDATED = "2024/09/09"

# Groqクライアントのセットアップ
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, chunk=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
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
            wf.setnchannels(1)
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
                model="whisper-large-v3",
                prompt="""眼科医師の会話です。専門的な眼科用語と医学用語が使用されます。
                主な用語：眼圧, 網膜, 緑内障, 白内障, 黄斑変性, 視神経, 角膜, 虹彩, 水晶体, 結膜, 
                視力, 屈折, 眼底, 瞳孔, 硝子体, 視野, 眼筋, 涙腺, 眼窩, 斜視
                これらの用語と数値・測定値の正確な認識に注意してください。""",
                response_format="text",
                language="ja",
            )
        return transcription
    except Exception as e:
        print(f"文字起こし中にエラーが発生しました: {str(e)}")
        return None


def copy_transcription_to_clipboard(text):
    if text:
        pyperclip.copy(text)


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

        self.status_label = tk.Label(master, text="Pauseキーで録音開始/停止")
        self.status_label.pack(pady=5)

        # Pauseキーのイベントリスナーを設定
        keyboard.on_press_key("pause", self.on_pause_key)

    def toggle_recording(self):
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        try:
            self.recorder.start_recording()
            self.record_button.config(text='録音停止')
            self.status_label.config(text="録音中... (Pauseキーで停止)")
            threading.Thread(target=self.recorder.record, daemon=True).start()
        except Exception as e:
            print(f"録音の開始中にエラーが発生しました: {str(e)}")
            self.record_button.config(text='録音開始')

    def stop_recording(self):
        try:
            frames, sample_rate = self.recorder.stop_recording()
            self.record_button.config(text='録音開始')
            self.status_label.config(text="Pauseキーで録音開始/停止")
            threading.Thread(target=self.process_audio, args=(frames, sample_rate), daemon=True).start()
        except Exception as e:
            print(f"録音の停止中にエラーが発生しました: {str(e)}")

    def on_pause_key(self, e):
        self.master.after(0, self.toggle_recording)

    def process_audio(self, frames, sample_rate):
        temp_audio_file = save_audio(frames, sample_rate)
        if temp_audio_file:
            transcription = transcribe_audio(temp_audio_file)
            if transcription:
                self.master.after(0, self.update_transcription, transcription)
            try:
                os.unlink(temp_audio_file)
            except Exception as e:
                print(f"一時ファイルの削除中にエラーが発生しました: {str(e)}")

    def update_transcription(self, text):
        self.transcription_text.delete('1.0', tk.END)
        self.transcription_text.insert(tk.END, text)
        self.transcription_text.see(tk.END)

    def copy_to_clipboard(self):
        text = self.transcription_text.get('1.0', tk.END).strip()
        copy_transcription_to_clipboard(text)
        print("テキストをクリップボードにコピーしました。")


def main():
    root = tk.Tk()
    gui = AudioRecorderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
