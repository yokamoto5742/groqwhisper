import tkinter as tk
import pytest
import re
from unittest.mock import MagicMock, patch
from app_ui_components import UIComponents

# テスト用の設定データ
CONFIG = {
    "WINDOW": {
        "width": 350,
        "height": 400  # 高さを400に修正
    },
    "KEYS": {
        "TOGGLE_RECORDING": "F1",
        "TOGGLE_PUNCTUATION": "F2",
        "RELOAD_AUDIO": "F4",  # RELOAD_AUDIOキーを追加
        "EXIT_APP": "F3"
    },
    "PATHS": {  # PATHSセクションを追加
        "TEMP_DIR": "./temp"
    }
}

# テスト用のコールバック関数
CALLBACKS = {
    "toggle_recording": MagicMock(),
    "toggle_punctuation": MagicMock()
}


@pytest.fixture
def ui_components():
    master = tk.Tk()
    return UIComponents(master, CONFIG, CALLBACKS)


def test_setup_ui(ui_components):
    version = "1.0.0"
    ui_components.setup_ui(version)

    # ウィンドウタイトルの確認
    assert ui_components.master.title() == f"音声入力メモ v{version}"

    # ウィンドウサイズの確認
    ui_components.master.update_idletasks()
    actual_geometry = ui_components.master.geometry()
    assert re.match(r"350x400\+\d+\+\d+", actual_geometry)  # 高さを400に修正

    # ボタンのテキスト確認
    assert ui_components.record_button.cget("text") == "音声入力開始"
    assert ui_components.punctuation_button.cget("text") == f"句読点切替:{CONFIG['KEYS']['TOGGLE_PUNCTUATION']}"
    assert ui_components.reload_audio_button.cget(
        "text") == f"音声再読込:{CONFIG['KEYS']['RELOAD_AUDIO']}"  # 音声再読込ボタンのテキスト確認を追加
    assert ui_components.close_button.cget("text") == f"閉じる:{CONFIG['KEYS']['EXIT_APP']}"

    # ラベルのテキスト確認
    assert ui_components.punctuation_status_label.cget("text") == "【現在句読点あり】"  # 【】を追加
    assert ui_components.status_label.cget("text") == f"{CONFIG['KEYS']['TOGGLE_RECORDING']}キーで音声入力開始/停止"


def test_update_record_button(ui_components):
    ui_components.setup_ui("1.0.0")

    # 録音中の状態
    ui_components.update_record_button(True)
    assert ui_components.record_button.cget("text") == f"音声入力停止:{CONFIG['KEYS']['TOGGLE_RECORDING']}"

    # 録音停止中の状態
    ui_components.update_record_button(False)
    assert ui_components.record_button.cget("text") == f"音声入力開始:{CONFIG['KEYS']['TOGGLE_RECORDING']}"


def test_update_status_label(ui_components):
    ui_components.setup_ui("1.0.0")

    # ステータスラベルの更新
    new_text = "テストメッセージ"
    ui_components.update_status_label(new_text)
    assert ui_components.status_label.cget("text") == new_text


def test_update_punctuation_button(ui_components):
    ui_components.setup_ui("1.0.0")

    # 句読点ありの状態
    ui_components.update_punctuation_button(True)
    assert ui_components.punctuation_status_label.cget("text") == "【現在句読点あり】"  # 【】を追加

    # 句読点なしの状態
    ui_components.update_punctuation_button(False)
    assert ui_components.punctuation_status_label.cget("text") == "【現在句読点なし】"  # 【】を追加


@patch("pyautogui.hotkey")
def test_open_clipboard_history(mock_hotkey, ui_components):
    ui_components.open_clipboard_history()
    mock_hotkey.assert_called_once_with("win", "v")


def test_open_replacements_editor(ui_components):
    with patch("app_ui_components.ReplacementsEditor") as mock_editor:
        ui_components.open_replacements_editor()
        mock_editor.assert_called_once_with(ui_components.master, CONFIG)


# 新しいテストケースを追加
@patch("glob.glob")
@patch("os.path.getmtime")
def test_get_latest_audio_file(mock_getmtime, mock_glob, ui_components):
    mock_glob.return_value = ["file1.wav", "file2.wav"]
    mock_getmtime.return_value = 12345

    result = ui_components.get_latest_audio_file()
    assert result == "file1.wav"  # 最新のファイルを返すことを確認


@patch("tkinter.filedialog.askopenfilename")
def test_open_audio_file(mock_askopenfilename, ui_components):
    ui_components.setup_ui("1.0.0")
    mock_askopenfilename.return_value = "test.wav"

    ui_components.open_audio_file()
    mock_askopenfilename.assert_called_once_with(
        title='音声ファイルを選択',
        filetypes=[('Wave files', '*.wav')],
        initialdir=CONFIG['PATHS']['TEMP_DIR']
    )
