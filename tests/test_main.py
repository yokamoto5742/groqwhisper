import pytest
from unittest.mock import patch, MagicMock
import main


@pytest.fixture
def mock_dependencies():
    with patch('main.load_config') as mock_load_config, \
            patch('main.AudioRecorder') as mock_audio_recorder, \
            patch('main.setup_groq_client') as mock_setup_groq_client, \
            patch('main.load_replacements') as mock_load_replacements, \
            patch('main.tk.Tk') as mock_tk, \
            patch('main.AudioRecorderGUI') as mock_audio_recorder_gui:
        mock_load_config.return_value = {'mock': 'config'}
        mock_audio_recorder.return_value = MagicMock()
        mock_setup_groq_client.return_value = MagicMock()
        mock_load_replacements.return_value = {'old': 'new'}
        mock_tk.return_value = MagicMock()
        mock_audio_recorder_gui.return_value = MagicMock()

        yield {
            'load_config': mock_load_config,
            'AudioRecorder': mock_audio_recorder,
            'setup_groq_client': mock_setup_groq_client,
            'load_replacements': mock_load_replacements,
            'tk': mock_tk,
            'AudioRecorderGUI': mock_audio_recorder_gui
        }


def test_main_function(mock_dependencies):
    # mainの実行
    main.main()

    # 各依存関数が正しく呼び出されたことを確認
    mock_dependencies['load_config'].assert_called_once()
    mock_dependencies['AudioRecorder'].assert_called_once_with({'mock': 'config'})
    mock_dependencies['setup_groq_client'].assert_called_once()
    mock_dependencies['load_replacements'].assert_called_once()
    mock_dependencies['tk'].assert_called_once()

    # AudioRecorderGUIが正しく初期化されたことを確認
    mock_dependencies['AudioRecorderGUI'].assert_called_once()
    args = mock_dependencies['AudioRecorderGUI'].call_args[0]
    assert isinstance(args[0], MagicMock)  # root
    assert args[1] == {'mock': 'config'}  # config
    assert isinstance(args[2], MagicMock)  # recorder
    assert isinstance(args[3], MagicMock)  # client
    assert args[4] == {'old': 'new'}  # replacements
    assert args[5] == "1.0.3"  # VERSION

    # mainloopが呼び出されたことを確認
    mock_dependencies['tk'].return_value.mainloop.assert_called_once()


def test_version_constant():
    assert main.VERSION == "1.0.3"


def test_last_updated_constant():
    assert main.LAST_UPDATED == "2024/10/05"


if __name__ == "__main__":
    pytest.main()
