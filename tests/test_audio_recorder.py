import pytest
from unittest.mock import patch
import tempfile
import os
import wave
import pyaudio
from src.audio_recorder import AudioRecorder, save_audio

def test_audio_recorder_init():
    config = {'AUDIO': {'SAMPLE_RATE': '44100', 'CHANNELS': '1', 'CHUNK': '1024'}}
    recorder = AudioRecorder(config)
    assert recorder.sample_rate == 44100
    assert recorder.channels == 1
    assert recorder.chunk == 1024

@pytest.mark.skip(reason="PyAudioの初期化が必要なため、CIでは実行できない")
def test_audio_recorder_start_stop():
    config = {'AUDIO': {'SAMPLE_RATE': '44100', 'CHANNELS': '1', 'CHUNK': '1024'}}
    recorder = AudioRecorder(config)
    recorder.start_recording()
    assert recorder.is_recording == True
    frames, sample_rate = recorder.stop_recording()
    assert recorder.is_recording == False
    assert len(frames) > 0
    assert sample_rate == 44100

def test_save_audio():
    frames = [b'\x00' * 1024] * 10  # ダミーのオーディオフレーム
    config = {'AUDIO': {'CHANNELS': '1'}}
    with patch('wave.open'):
        file_path = save_audio(frames, 44100, config)
    assert file_path is not None
    assert file_path.endswith('.wav')
