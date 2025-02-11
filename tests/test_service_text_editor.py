import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import os
from configparser import ConfigParser
from service_text_editor import ReplacementsEditor


class MockText(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._values = {}

    def __setitem__(self, key, value):
        self._values[key] = value

    def __getitem__(self, key):
        return self._values.get(key)


@pytest.fixture
def mock_config():
    config = ConfigParser()
    config['PATHS'] = {'replacements_file': 'test_replacements.txt'}
    config['EDITOR'] = {
        'width': '400',
        'height': '700',
        'font_name': 'MS Gothic',
        'font_size': '12'
    }
    return config


@pytest.fixture
def mock_tk():
    with patch('tkinter.Tk') as mock:
        mock_root = MagicMock()
        mock.return_value = mock_root
        yield mock_root


@pytest.fixture
def mock_toplevel():
    with patch('tkinter.Toplevel') as mock:
        mock_window = MagicMock()
        mock.return_value = mock_window
        yield mock_window


@pytest.fixture
def mock_text():
    text = MockText()
    text.pack = MagicMock()
    text.insert = MagicMock()
    text.get = MagicMock()
    return text


@pytest.fixture
def mock_scrollbar():
    scrollbar = MagicMock()
    scrollbar.set = MagicMock()
    return scrollbar


@pytest.fixture(autouse=True)  # 追加：自動実行フィクスチャ
def cleanup_tk():
    yield
    while tk._default_root:  # 追加
        tk._default_root.destroy()


@pytest.fixture
def editor(mock_config, mock_tk, mock_toplevel, mock_text, mock_scrollbar):
    with patch('tkinter.ttk.Frame'), \
            patch('tkinter.ttk.Button'), \
            patch('tkinter.messagebox'), \
            patch('tkinter.Text', return_value=mock_text), \
            patch('tkinter.ttk.Scrollbar', return_value=mock_scrollbar):
        editor = ReplacementsEditor(mock_tk, mock_config)
        editor.text_area._values['yscrollcommand'] = mock_scrollbar.set
        yield editor
        editor.window.destroy() # テスト終了時にウィンドウを破棄


def test_init_with_invalid_config():
    invalid_config = ConfigParser()
    with pytest.raises(ValueError) as exc_info:
        ReplacementsEditor(Mock(), invalid_config)
    assert 'コンフィグにreplacements_fileのパス設定がありません' in str(exc_info.value)


def test_load_file_existing(editor, tmp_path):
    test_file = tmp_path / "test_replacements.txt"
    test_content = "old,new\ntest,テスト"
    test_file.write_text(test_content, encoding='utf-8')

    editor.config['PATHS']['replacements_file'] = str(test_file)

    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = test_content
        editor.load_file()

    editor.text_area.insert.assert_called_with('1.0', test_content)


def test_load_file_not_existing(editor, tmp_path):
    non_existent_file = tmp_path / "non_existent.txt"
    editor.config['PATHS']['replacements_file'] = str(non_existent_file)

    with patch('tkinter.messagebox.showwarning') as mock_warning, \
            patch('os.path.exists', return_value=False), \
            patch('builtins.open', create=True) as mock_open:
        mock_open.side_effect = FileNotFoundError()
        editor.load_file()
        mock_warning.assert_called_once()
        assert '新規作成します' in mock_warning.call_args[0][1]


def test_load_file_error(editor):
    editor.config['PATHS']['replacements_file'] = '/invalid/path/file.txt'

    with patch('os.path.exists', return_value=True), \
            patch('builtins.open', side_effect=Exception('テストエラー')), \
            patch('tkinter.messagebox.showerror') as mock_error:
        editor.load_file()
        mock_error.assert_called_once()
        assert 'ファイルの読み込みに失敗しました' in mock_error.call_args[0][1]


def test_save_file_success(editor, tmp_path):
    test_file = tmp_path / "test_replacements.txt"
    editor.config['PATHS']['replacements_file'] = str(test_file)
    test_content = "old,new\ntest,テスト"

    editor.text_area.get.return_value = test_content

    with patch('tkinter.messagebox.showinfo') as mock_info:
        editor.save_file()

        assert test_file.exists()
        assert test_file.read_text(encoding='utf-8') == test_content
        mock_info.assert_called_once()
        assert '保存完了' in mock_info.call_args[0][0]
        editor.window.destroy.assert_called_once()


def test_save_file_error(editor):
    editor.config['PATHS']['replacements_file'] = '/invalid/path/file.txt'
    editor.text_area.get.return_value = "test content"

    with patch('os.makedirs', side_effect=Exception('テストエラー')), \
            patch('tkinter.messagebox.showerror') as mock_error:
        editor.save_file()
        mock_error.assert_called_once()
        assert 'ファイルの保存に失敗しました' in mock_error.call_args[0][1]


def test_window_setup(editor):
    editor.window.title.assert_called_once_with('テキスト置換登録( 置換前 , 置換後 )')
    editor.window.geometry.assert_called_once()
    editor.window.transient.assert_called_once()
    editor.window.grab_set.assert_called_once()


def test_text_area_setup(editor):
    # テキストエリアの設定を確認
    assert editor.text_area is not None
    assert editor.text_area.pack.called
    # スクロールバーの設定を確認
    assert 'yscrollcommand' in editor.text_area._values
    assert callable(editor.text_area._values['yscrollcommand'])
