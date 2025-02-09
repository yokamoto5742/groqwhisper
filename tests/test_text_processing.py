import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from service_text_processing import (
    get_replacements_path,
    load_replacements,
    replace_text,
    copy_and_paste_transcription
)

@pytest.fixture
def sample_replacements():
    return {
        'old1': 'new1',
        'old2': 'new2',
        'テスト': 'TEST'
    }

@pytest.fixture
def sample_config():
    return {
        'CLIPBOARD': {
            'PASTE_DELAY': '0.1'
        }
    }

def test_get_replacements_path():
    # frozen環境でない場合のテスト
    with patch('sys.frozen', False, create=True):
        with patch('os.path.dirname') as mock_dirname:
            mock_dirname.return_value = '/test/path'
            expected_path = os.path.join('/test/path', 'replacements.txt')
            assert get_replacements_path() == expected_path

    # frozen環境の場合のテストはなし


def test_load_replacements(tmp_path):
    # テスト用の置換ファイルを作成
    replacements_file = tmp_path / "replacements.txt"
    replacements_file.write_text("""old1,new1
old2,new2
テスト,TEST
invalid_line
""", encoding='utf-8')

    with patch('service_text_processing.get_replacements_path', return_value=str(replacements_file)):
        result = load_replacements()
        assert result == {
            'old1': 'new1',
            'old2': 'new2',
            'テスト': 'TEST'
        }

def test_load_replacements_file_not_found():
    with patch('service_text_processing.get_replacements_path', return_value='nonexistent.txt'):
        result = load_replacements()
        assert result == {}

def test_replace_text(sample_replacements):
    # 正常系のテスト
    input_text = "これはold1とold2とテストです。"
    expected = "これはnew1とnew2とTESTです。"
    assert replace_text(input_text, sample_replacements) == expected

    # 空の入力テキストのテスト
    assert replace_text("", sample_replacements) == ""

    # 空の置換ルールのテスト
    assert replace_text("テストテキスト", {}) == "テストテキスト"

@patch('pyperclip.copy')
@patch('threading.Timer')
def test_copy_and_paste_transcription(mock_timer, mock_copy, sample_replacements, sample_config):
    test_text = "これはold1とテストです。"
    expected_text = "これはnew1とTESTです。"

    # タイマーオブジェクトのモック
    mock_timer_instance = MagicMock()
    mock_timer.return_value = mock_timer_instance

    copy_and_paste_transcription(test_text, sample_replacements, sample_config)

    # クリップボードにコピーされたテキストの検証
    mock_copy.assert_called_once_with(expected_text)

    # タイマーの設定が正しいことを検証
    mock_timer.assert_called_once()
    assert mock_timer.call_args[0][0] == 0.1  # PASTE_DELAYの値
    mock_timer_instance.start.assert_called_once()

def test_copy_and_paste_transcription_empty_text(sample_replacements, sample_config):
    # 空のテキストの場合、何も実行されないことを確認
    result = copy_and_paste_transcription("", sample_replacements, sample_config)
    assert result is None
