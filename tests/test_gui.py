import pytest
from unittest.mock import Mock
import tkinter as tk
from app_window import AudioRecorderGUI
from config_manager import load_config


@pytest.fixture
def gui_setup():
    root = tk.Tk()
    config = load_config()
    recorder = Mock()
    client = Mock()
    replacements = {}
    gui = AudioRecorderGUI(root, config, recorder, client, replacements, "1.0.0")
    return gui


def test_gui_init(gui_setup):
    gui = gui_setup
    assert isinstance(gui.record_button, tk.Button)
    assert isinstance(gui.transcription_text, tk.Text)


def test_gui_toggle_recording(gui_setup):
    gui = gui_setup
    gui.recorder.is_recording = False
    gui.toggle_recording()
    gui.recorder.start_recording.assert_called_once()

    gui.recorder.is_recording = True
    gui.toggle_recording()
    gui.recorder.stop_recording.assert_called_once()
