import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))


def create_mock_config():
    config_data = {
        'AUDIO': {
            'SAMPLE_RATE': 16000,
            'CHANNELS': 1,
            'CHUNK': 1024
        },
        'WHISPER': {
            'MODEL': 'whisper-large-v3',
            'LANGUAGE': 'ja',
            'PROMPT': '眼科医師の会話です',
            'USE_PUNCTUATION': True,
            'USE_COMMA': True
        },
        'UI': {
            'TEXT_AREA_HEIGHT': 20,
            'TEXT_AREA_WIDTH': 50,
            'TEXT_AREA_PADY': 5
        },
        'CLIPBOARD': {
            'PASTE_DELAY': 0.5
        },
        'OPTIONS': {
            'START_MINIMIZED': True
        },
        'KEYS': {
            'TOGGLE_RECORDING': 'f9',
            'EXIT_APP': 'esc',
            'TOGGLE_PUNCTUATION': 'pause',
            'TOGGLE_COMMA': 'pause'
        },
        'RECORDING': {
            'AUTO_STOP_TIMER': 120
        }
    }

    class CaseInsensitiveDict(dict):
        def __getitem__(self, key):
            return super().__getitem__(key.upper())

        def __contains__(self, key):
            return super().__contains__(key.upper())

        # getbooleanメソッドを追加
        def getboolean(self, key, fallback=None):
            value = self.get(key.upper(), fallback)
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes', 'on']
            return bool(value)

    mock_config = MagicMock()
    mock_config.__getitem__.side_effect = lambda key: CaseInsensitiveDict(
        {k.upper(): v if not isinstance(v, dict) else CaseInsensitiveDict(v) for k, v in
         config_data.get(key.upper(), {}).items()})
    mock_config.__contains__.side_effect = lambda key: key.upper() in config_data
    return mock_config


@patch('tkinter.Tk')
@patch('src.gui.AudioRecorderGUI')
@patch('src.audio_recorder.AudioRecorder')
@patch('src.transcription.setup_groq_client')
@patch('src.text_processing.load_replacements')
@patch('config.config.load_config')
def test_main(mock_load_config, mock_load_replacements, mock_setup_groq_client, mock_audio_recorder, mock_gui, mock_tk):
    # 詳細なConfigのモックを設定
    mock_config = create_mock_config()
    mock_load_config.return_value = mock_config

    from src.main import main
    main()

    mock_tk.assert_called_once()
    mock_load_config.assert_called_once()
    mock_audio_recorder.assert_called_once_with(mock_config)
    mock_setup_groq_client.assert_called_once()
    mock_load_replacements.assert_called_once()
    mock_gui.assert_called_once()

    # デバッグ用: AudioRecorderの引数を出力
    print(f"デバック用AudioRecorder was called with: {mock_audio_recorder.call_args_list}")

    # GUIの初期化パラメータを確認
    mock_gui.assert_called_once_with(
        mock_tk.return_value,
        mock_config,
        mock_audio_recorder.return_value,
        mock_setup_groq_client.return_value,
        mock_load_replacements.return_value,
    )
