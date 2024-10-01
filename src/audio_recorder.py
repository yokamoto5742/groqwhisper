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
            self.logger.info("録音を開始しました。")
        except OSError as e:
            self.logger.error(f"録音の開始中にOSエラーが発生しました: {e}")
        except Exception as e:
            self.logger.error(f"録音の開始中に予期せぬエラーが発生しました: {e}")

    def stop_recording(self) -> Tuple[List[bytes], int]:
        self.is_recording = False
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
            self.logger.info("録音を停止しました。")
        except OSError as e:
            self.logger.error(f"録音の停止中にOSエラーが発生しました: {e}")
        except Exception as e:
            self.logger.error(f"録音の停止中に予期せぬエラーが発生しました: {e}")
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
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            wf = wave.open(temp_audio.name, "wb")
            wf.setnchannels(int(config['AUDIO']['CHANNELS']))
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(frames))
            wf.close()
            logging.info(f"音声ファイルを保存しました: {temp_audio.name}")
            return temp_audio.name
    except wave.Error as e:
        logging.error(f"WAVファイルの作成中にエラーが発生しました: {e}")
    except IOError as e:
        logging.error(f"ファイルI/O操作中にエラーが発生しました: {e}")
    except Exception as e:
        logging.error(f"音声ファイルの保存中に予期せぬエラーが発生しました: {e}")
    return None
