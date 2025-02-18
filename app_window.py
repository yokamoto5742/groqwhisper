import logging
import tkinter as tk
import os
from typing import Optional, Dict, Any

from app_ui_components import UIComponents
from service_keyboard_handler import KeyboardHandler
from service_recording_controller import RecordingController
from service_transcription import transcribe_audio
from service_notification import NotificationManager
from config_manager import save_config


class VoiceInputManager:
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

        self.ui_components = UIComponents(master, config, {})

        callbacks = {
            'toggle_recording': self.toggle_recording,
            'toggle_punctuation': self.toggle_punctuation,
            'reload_audio': self.ui_components.reload_latest_audio,
        }

        self.ui_components.update_callbacks(callbacks)
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
            },
            self.notification_manager.show_timed_message
        )

        self.keyboard_handler = KeyboardHandler(
            master,
            config,
            self.toggle_recording,
            self.toggle_punctuation,
            self.ui_components.reload_latest_audio,
            self.close_application,
        )

        self.client = client
        self.master.bind('<<LoadAudioFile>>', self.recording_controller.handle_audio_file)

        start_minimized = self.config['OPTIONS'].getboolean('START_MINIMIZED', True)
        if start_minimized:
            self.master.iconify()

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def toggle_recording(self):
        self.recording_controller.toggle_recording()

    def toggle_punctuation(self):
        use_punctuation = not self.recording_controller.use_punctuation
        self.recording_controller.use_punctuation = use_punctuation
        self.recording_controller.use_comma = use_punctuation
        self.ui_components.update_punctuation_button(use_punctuation)
        logging.info(f"現在句読点: {'あり' if use_punctuation else 'なし'}")
        self.config['WHISPER']['USE_PUNCTUATION'] = str(use_punctuation)
        self.config['WHISPER']['USE_COMMA'] = str(use_punctuation)
        save_config(self.config)

    def close_application(self):
        self.recording_controller.cleanup()
        self.keyboard_handler.cleanup()
        self.notification_manager.cleanup()
        self.master.quit()
