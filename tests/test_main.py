import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
import sys
import os

# テスト対象のモジュールをインポート
from main import main


# フィクスチャの定義
@pytest.fixture
def mock_dependencies():
    with patch('main.load_config') as mock_config, \
            patch('main.setup_logging') as mock_logging, \
            patch('main.AudioRecorder') as mock_recorder, \
            patch('main.setup_groq_client') as mock_client, \
            patch('main.load_replacements') as mock_replacements, \
            patch('main.tk.Tk') as mock_tk, \
            patch('main.VoiceInputManager') as mock_app:
        # モックの戻り値を設定
        mock_config.return_value = {'logging': {'log_dir': 'test_logs'}}
        mock_recorder.return_value = MagicMock()
        mock_client.return_value = MagicMock()
        mock_replacements.return_value = {}

        # Tkインターフェースのモック
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        yield {
            'config': mock_config,
            'logging': mock_logging,
            'recorder': mock_recorder,
            'client': mock_client,
            'replacements': mock_replacements,
            'tk': mock_tk,
            'app': mock_app,
            'root': mock_root
        }


def test_main_success(mock_dependencies):
    """正常系のメインフロー実行テスト"""
    # テスト実行
    main()

    # 各依存モジュールが1回ずつ呼ばれることを確認
    mock_dependencies['config'].assert_called_once()
    mock_dependencies['logging'].assert_called_once()
    mock_dependencies['recorder'].assert_called_once()
    mock_dependencies['client'].assert_called_once()
    mock_dependencies['replacements'].assert_called_once()
    mock_dependencies['tk'].assert_called_once()
    mock_dependencies['app'].assert_called_once()

    # mainloopが呼ばれることを確認
    mock_dependencies['root'].mainloop.assert_called_once()

def test_app_close_handling(mock_dependencies):
    """アプリケーション終了処理のテスト"""
    # メイン処理を実行
    main()

    # VoiceInputManagerのインスタンスを取得
    app_instance = mock_dependencies['app'].return_value

    # WM_DELETE_WINDOWプロトコルが正しく設定されていることを確認
    mock_dependencies['root'].protocol.assert_called_once_with(
        "WM_DELETE_WINDOW",
        app_instance.close_application
    )
