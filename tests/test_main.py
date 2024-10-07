import pytest
from unittest.mock import patch, MagicMock
import main
import configparser


@pytest.fixture
def mock_dependencies():
    with patch('main.load_config') as mock_load_config, \
            patch('main.AudioRecorder') as mock_audio_recorder, \
            patch('main.setup_groq_client') as mock_setup_groq_client, \
            patch('main.load_replacements') as mock_load_replacements, \
            patch('main.tk.Tk') as mock_tk, \
            patch('main.AudioRecorderGUI') as mock_audio_recorder_gui, \
            patch('main.setup_logging') as mock_setup_logging:
        mock_config = configparser.ConfigParser()
        mock_config['Logging'] = {'log_directory': 'mock_logs'}
        mock_load_config.return_value = mock_config

        mock_audio_recorder.return_value = MagicMock()
        mock_setup_groq_client.return_value = MagicMock()
        mock_load_replacements.return_value = {'old': 'new'}
        mock_tk.return_value = MagicMock()
        mock_audio_recorder_gui.return_value = MagicMock()
        mock_setup_logging.return_value = None

        yield {
            'load_config': mock_load_config,
            'AudioRecorder': mock_audio_recorder,
            'setup_groq_client': mock_setup_groq_client,
            'load_replacements': mock_load_replacements,
            'tk': mock_tk,
            'AudioRecorderGUI': mock_audio_recorder_gui,
            'setup_logging': mock_setup_logging
        }


def test_main_function(mock_dependencies):
    # mainの実行
    main.main()

    # 各依存関数が正しく呼び出されたことを確認
    mock_dependencies['load_config'].assert_called_once()
    mock_dependencies['setup_logging'].assert_called_once()
    mock_dependencies['AudioRecorder'].assert_called_once()
    mock_dependencies['setup_groq_client'].assert_called_once()
    mock_dependencies['load_replacements'].assert_called_once()
    mock_dependencies['tk'].assert_called_once()

    # AudioRecorderGUIが正しく初期化されたことを確認
    mock_dependencies['AudioRecorderGUI'].assert_called_once()
    args = mock_dependencies['AudioRecorderGUI'].call_args[0]
    assert isinstance(args[0], MagicMock)  # root
    assert isinstance(args[1], configparser.ConfigParser)  # config
    assert isinstance(args[2], MagicMock)  # recorder
    assert isinstance(args[3], MagicMock)  # client
    assert args[4] == {'old': 'new'}  # replacements
    assert args[5] == main.VERSION  # VERSION

    # mainloopが呼び出されたことを確認
    mock_dependencies['tk'].return_value.mainloop.assert_called_once()


if __name__ == "__main__":
    pytest.main()
