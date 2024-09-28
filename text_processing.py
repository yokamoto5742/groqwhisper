import pyperclip
import pyautogui
import threading


def load_replacements(file_path='replacements.txt'):
    replacements = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            old, new = line.strip().split(',')
            replacements[old] = new
    return replacements


def replace_text(text, replacements):
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def copy_and_paste_transcription(text, replacements, config):
    if text:
        replaced_text = replace_text(text, replacements)
        pyperclip.copy(replaced_text)
        paste_delay = float(config['CLIPBOARD']['PASTE_DELAY'])
        threading.Timer(paste_delay, lambda: pyautogui.hotkey('ctrl', 'v')).start()
