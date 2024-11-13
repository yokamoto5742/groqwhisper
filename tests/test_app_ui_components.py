import pytest
import tkinter as tk
from unittest.mock import Mock, MagicMock
from app_ui_components import UIComponents


@pytest.fixture
def mock_config():
    return {
        'UI': {
            'TEXT_AREA_HEIGHT': '10',
            'TEXT_AREA_WIDTH': '50',
            'TEXT_AREA_PADY': '5'
        },
        'KEYS': {
            'TOGGLE_RECORDING': 'F6',
            'TOGGLE_PUNCTUATION': 'F7',
            'TOGGLE_COMMA': 'F8',
            'EXIT_APP': 'F12'
        }
    }


@pytest.fixture
def mock_callbacks():
    return {
        'toggle_recording': Mock(),
        'copy': Mock(),
        'clear': Mock(),
        'toggle_comma': Mock(),
        'toggle_punctuation': Mock()
    }


@pytest.fixture
def mock_text():
    text = MagicMock()
    text.get = MagicMock(return_value="")
    text.delete = MagicMock()
    text.insert = MagicMock()
    text.see = MagicMock()
    text.pack = MagicMock()
    return text


@pytest.fixture
def mock_button():
    button = MagicMock()
    button.config = MagicMock()
    button.pack = MagicMock()
    return button


@pytest.fixture
def mock_label():
    label = MagicMock()
    label.config = MagicMock()
    label.pack = MagicMock()
    return label


@pytest.fixture
def ui_components(mock_config, mock_callbacks, monkeypatch, mock_text, mock_button, mock_label):
    # tkinterのウィンドウ作成をモック化
    mock_root = MagicMock()
    mock_root.title = MagicMock()

    # tkinterのウィジェット作成をモック化
    def mock_button_init(*args, **kwargs):
        b = MagicMock()
        b.config = mock_button.config
        b.pack = mock_button.pack
        if 'text' in kwargs:
            b._mock_text = kwargs['text']  # テキストを保存
        return b

    def mock_text_init(*args, **kwargs):
        return mock_text

    def mock_label_init(*args, **kwargs):
        l = MagicMock()
        l.config = mock_label.config
        l.pack = mock_label.pack
        if 'text' in kwargs:
            l._mock_text = kwargs['text']  # テキストを保存
        return l

    monkeypatch.setattr(tk, "Button", mock_button_init)
    monkeypatch.setattr(tk, "Text", mock_text_init)
    monkeypatch.setattr(tk, "Label", mock_label_init)

    ui = UIComponents(
        mock_root,
        mock_config,
        mock_callbacks['toggle_recording'],
        mock_callbacks['copy'],
        mock_callbacks['clear'],
        mock_callbacks['toggle_comma'],
        mock_callbacks['toggle_punctuation']
    )
    ui.setup_ui('1.0')
    return ui

def test_update_record_button(ui_components):
    """録音ボタンの状態更新テスト"""
    ui_components.update_record_button(True)
    ui_components.record_button.config.assert_called_with(text='音声入力停止')

    ui_components.update_record_button(False)
    ui_components.record_button.config.assert_called_with(text='音声入力開始')


def test_update_punctuation_button(ui_components, mock_config):
    """句点ボタンの状態更新テスト"""
    ui_components.update_punctuation_button(True)
    ui_components.punctuation_button.config.assert_called_with(
        text=f'句点(。)あり:{mock_config["KEYS"]["TOGGLE_PUNCTUATION"]}'
    )

    ui_components.update_punctuation_button(False)
    ui_components.punctuation_button.config.assert_called_with(
        text=f'句点(。)なし:{mock_config["KEYS"]["TOGGLE_PUNCTUATION"]}'
    )


def test_update_comma_button(ui_components, mock_config):
    """読点ボタンの状態更新テスト"""
    ui_components.update_comma_button(True)
    ui_components.comma_button.config.assert_called_with(
        text=f'読点(、)あり:{mock_config["KEYS"]["TOGGLE_COMMA"]}'
    )

    ui_components.update_comma_button(False)
    ui_components.comma_button.config.assert_called_with(
        text=f'読点(、)なし:{mock_config["KEYS"]["TOGGLE_COMMA"]}'
    )


def test_append_transcription(ui_components, mock_text):
    """文字起こしテキストの追加テスト"""
    test_text1 = "テスト文章1"
    test_text2 = "テスト文章2"

    # 空のテキストエリアにテキストを追加
    mock_text.get.return_value = ""
    ui_components.append_transcription(test_text1)
    mock_text.insert.assert_called_with(tk.END, test_text1)

    # 既存のテキストがある状態でテキストを追加
    mock_text.get.return_value = test_text1
    ui_components.append_transcription(test_text2)
    assert mock_text.insert.call_args_list[-2:] == [
        ((tk.END, "\n"),),
        ((tk.END, test_text2),)
    ]


def test_get_transcription_text(ui_components, mock_text):
    """文字起こしテキスト取得テスト"""
    test_text = "テスト文章"
    mock_text.get.return_value = test_text

    result = ui_components.get_transcription_text()
    mock_text.get.assert_called_with('1.0', tk.END)
    assert result == test_text


def test_clear_transcription_text(ui_components, mock_text):
    """文字起こしテキストのクリアテスト"""
    ui_components.clear_transcription_text()
    mock_text.delete.assert_called_with('1.0', tk.END)


def test_callback_execution(ui_components, mock_callbacks):
    """コールバック関数の実行テスト"""
    # invokeメソッドをモックに追加
    ui_components.record_button.invoke = lambda: mock_callbacks['toggle_recording']()
    ui_components.copy_button.invoke = lambda: mock_callbacks['copy']()
    ui_components.clear_button.invoke = lambda: mock_callbacks['clear']()
    ui_components.comma_button.invoke = lambda: mock_callbacks['toggle_comma']()
    ui_components.punctuation_button.invoke = lambda: mock_callbacks['toggle_punctuation']()

    # テストの実行
    ui_components.record_button.invoke()
    mock_callbacks['toggle_recording'].assert_called_once()

    ui_components.copy_button.invoke()
    mock_callbacks['copy'].assert_called_once()

    ui_components.clear_button.invoke()
    mock_callbacks['clear'].assert_called_once()

    ui_components.comma_button.invoke()
    mock_callbacks['toggle_comma'].assert_called_once()

    ui_components.punctuation_button.invoke()
    mock_callbacks['toggle_punctuation'].assert_called_once()


def test_update_status_label(ui_components):
    """ステータスラベルの更新テスト"""
    test_status = "テストステータス"
    ui_components.update_status_label(test_status)
    ui_components.status_label.config.assert_called_with(text=test_status)
