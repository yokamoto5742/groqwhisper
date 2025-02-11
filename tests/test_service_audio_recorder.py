import pytest
from unittest.mock import Mock, patch
import pyaudio
import wave
import tempfile
from service_audio_recorder import AudioRecorder, save_audio


@pytest.fixture
def config():
    return {
        'AUDIO': {
            'SAMPLE_RATE': '44100',
            'CHANNELS': '2',
            'CHUNK': '1024'
        }
    }


@pytest.fixture
def mock_pyaudio():
    with patch('pyaudio.PyAudio') as mock:
        mock_stream = Mock()
        mock_stream.read.return_value = b'dummy_audio_data'
        mock.return_value.open.return_value = mock_stream
        mock.return_value.get_sample_size.return_value = 2
        yield mock


class TestAudioRecorder:
    def test_init(self, config):
        recorder = AudioRecorder(config)
        assert recorder.sample_rate == 44100
        assert recorder.channels == 2
        assert recorder.chunk == 1024
        assert recorder.frames == []
        assert not recorder.is_recording

    def test_start_recording(self, config, mock_pyaudio):
        recorder = AudioRecorder(config)
        recorder.start_recording()

        assert recorder.is_recording
        assert recorder.frames == []
        mock_pyaudio.assert_called_once()
        mock_pyaudio.return_value.open.assert_called_once_with(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )

    def test_stop_recording(self, config, mock_pyaudio):
        recorder = AudioRecorder(config)
        recorder.start_recording()
        frames, sample_rate = recorder.stop_recording()

        assert not recorder.is_recording
        assert sample_rate == 44100
        mock_pyaudio.return_value.open.return_value.stop_stream.assert_called_once()
        mock_pyaudio.return_value.open.return_value.close.assert_called_once()
        mock_pyaudio.return_value.terminate.assert_called_once()

    def test_record(self, config, mock_pyaudio):
        recorder = AudioRecorder(config)
        recorder.start_recording()

        # モックストリームがダミーデータを返すように設定
        mock_stream = mock_pyaudio.return_value.open.return_value
        mock_stream.read.return_value = b'dummy_audio_data'

        # 一時的にis_recordingをTrueに設定し、数回のループ後にFalseにする
        recorder.is_recording = True

        def side_effect(*args, **kwargs):
            recorder.is_recording = False
            return b'dummy_audio_data'

        mock_stream.read.side_effect = side_effect

        recorder.record()

        # フレームが1回分記録されていることを確認
        assert len(recorder.frames) == 1
        assert recorder.frames[0] == b'dummy_audio_data'

    @patch('pyaudio.PyAudio')
    @patch('wave.open')
    @patch('tempfile.NamedTemporaryFile')
    def test_save_audio(self, mock_temp_file, mock_wave_open, mock_pyaudio, config):
        frames = [b'dummy_audio_data']
        sample_rate = 44100

        mock_temp_file.return_value.name = 'test.wav'
        mock_wave_context = Mock()
        mock_wave_open.return_value.__enter__.return_value = mock_wave_context
        mock_pyaudio.return_value.get_sample_size.return_value = 2

        result = save_audio(frames, sample_rate, config)

        assert result == 'test.wav'
        mock_wave_context.setnchannels.assert_called_once_with(2)
        mock_wave_context.setsampwidth.assert_called_once_with(2)
        mock_wave_context.setframerate.assert_called_once_with(sample_rate)
        mock_wave_context.writeframes.assert_called_once_with(b'dummy_audio_data')
        mock_wave_open.assert_called_once_with('test.wav', 'wb')
