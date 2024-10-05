import os
import sys
import logging
import configparser
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from typing import Union, Any


def get_application_path() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config_path = os.path.join(get_application_path(), 'config.ini')
    config.read(config_path)
    return config


def setup_logging(config: configparser.ConfigParser) -> None:
    base_path = get_application_path()
    log_directory = os.path.join(base_path, config.get('Logging', 'log_directory', fallback='logs'))
    log_retention_days = config.getint('Logging', 'log_retention_days', fallback=7)

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file = os.path.join(log_directory, 'audio_recorder.log')

    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=log_retention_days
    )
    file_handler.suffix = "%Y-%m-%d.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[file_handler]
    )

    cleanup_old_logs(log_directory, log_retention_days)


def cleanup_old_logs(log_directory: str, retention_days: int) -> None:
    now = datetime.now()
    for filename in os.listdir(log_directory):
        if filename.endswith('.log') and filename != 'audio_recorder.log':
            file_path = os.path.join(log_directory, filename)
            file_modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_modification_time > timedelta(days=retention_days):
                os.remove(file_path)
                logging.info(f"古いログファイルを削除しました: {filename}")
