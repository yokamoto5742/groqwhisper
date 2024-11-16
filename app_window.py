import logging
from typing import Optional, Dict, Any

import tkinter as tk

from app_ui_components import UIComponents
from service_keyboard_handler import KeyboardHandler
from service_recording_controller import RecordingController
from service_notification import NotificationManager
from config_manager import save_config


class AudioRecorderGUI:
    def __init__(
            self,
            master: tk.Tk,
            config: Dict[str, Any],
            recorder: Any,
            client: Any,
            replacements: Dict[str, str],
            version: str
    ):
        self.master = master
        self.config = config
        self.version = version

        self.notification_manager = NotificationManager(master, config)

        self.ui_components = UIComponents(
            master,
            config,
            self.toggle_recording,
            self.copy_to_clipboard,
            self.clear_text,
            self.toggle_comma,
            self.toggle_punctuation
        )
        self.ui_components.setup_ui(version)

        self.recording_controller = RecordingController(
            master,
            config,
            recorder,
            client,
            replacements,
            {
                'update_record_button': self.ui_components.update_record_button,
                'update_status_label': self.ui_components.update_status_label,
                'append_transcription': self.ui_components.append_transcription
            },
            self.notification_manager.show_timed_message
        )

        self.keyboard_handler = KeyboardHandler(
            master,
            config,
            self.toggle_recording,
            self.toggle_punctuation,
            self.toggle_comma,
            self.close_application
        )

        start_minimized = self.config['OPTIONS'].getboolean('START_MINIMIZED', True)
        if start_minimized:
            self.master.iconify()

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def toggle_recording(self) -> None:
        self.recording_controller.toggle_recording()

    def toggle_punctuation(self) -> None:
        self.recording_controller.use_punctuation = not self.recording_controller.use_punctuation
        self.ui_components.update_punctuation_button(self.recording_controller.use_punctuation)
        logging.info(f"句点(。)モード: {'あり' if self.recording_controller.use_punctuation else 'なし'}")
        self.config['WHISPER']['USE_PUNCTUATION'] = str(self.recording_controller.use_punctuation)
        save_config(self.config)

    def toggle_comma(self) -> None:
        self.recording_controller.use_comma = not self.recording_controller.use_comma
        self.ui_components.update_comma_button(self.recording_controller.use_comma)
        logging.info(f"読点(、)モード: {'あり' if self.recording_controller.use_comma else 'なし'}")
        self.config['WHISPER']['USE_COMMA'] = str(self.recording_controller.use_comma)
        save_config(self.config)

    def copy_to_clipboard(self) -> None:
        text = self.ui_components.get_transcription_text()
        self.recording_controller.safe_copy_and_paste(text)

    def clear_text(self) -> None:
        self.ui_components.clear_transcription_text()

    def close_application(self) -> None:
        self.recording_controller.cleanup()
        self.keyboard_handler.cleanup()
        self.notification_manager.cleanup()
        self.master.quit()
