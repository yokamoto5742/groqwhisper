import pyaudio
import wave
import tempfile
import logging
from typing import List, Tuple, Optional


class AudioRecorder:
    def __init__(self, config: dict) -> None:
        self.sample_rate = int(config['AUDIO']['SAMPLE_RATE'])
        self.channels = int(config['AUDIO']['CHANNELS'])
        self.chunk = int(config['AUDIO']['CHUNK'])
        self.frames: List[bytes] = []
        self.is_recording = False
        self.p: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def start_recording(self) -> None:
        try:
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
            self.logger.info("音声入力を開始しました。")
        except OSError as e:
            self.logger.error(f"音声入力の開始中にOSエラーが発生しました: {e}")
        except Exception as e:
            self.logger.error(f"音声入力の開始中に予期せぬエラーが発生しました: {e}")

    def stop_recording(self) -> Tuple[List[bytes], int]:
        self.is_recording = False
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
            self.logger.info("音声入力を停止しました。")
        except OSError as e:
            self.logger.error(f"音声入力の停止中にOSエラーが発生しました: {e}")
        except Exception as e:
            self.logger.error(f"音声入力の停止中に予期せぬエラーが発生しました: {e}")
        return self.frames, self.sample_rate

    def record(self) -> None:
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
            except OSError as e:
                self.logger.error(f"音声入力中にOSエラーが発生しました: {e}")
                self.is_recording = False
                break
            except Exception as e:
                self.logger.error(f"音声入力中に予期せぬエラーが発生しました: {e}")
                self.is_recording = False
                break


def save_audio(frames: List[bytes], sample_rate: int, config: dict) -> Optional[str]:
    try:
        logging.info(f"音声ファイル保存開始: フレーム数={len(frames)}")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            wf = wave.open(temp_audio.name, "wb")
            channels = int(config['AUDIO']['CHANNELS'])

            wf.setnchannels(channels)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(frames))
            wf.close()

            logging.info(f"音声ファイル保存完了: {temp_audio.name}")
            return temp_audio.name
    except Exception as e:
        logging.error(f"音声ファイル保存エラー: {str(e)}")
        logging.debug(f"詳細: {traceback.format_exc()}")
        return None
