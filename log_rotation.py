import configparser
import logging
import os
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_path)
    return config


def setup_logging(config: configparser.ConfigParser):
    log_directory = os.path.join(os.path.dirname(__file__), config.get('LOGGING', 'log_directory', fallback='logs'))
    log_retention_days = config.getint('LOGGING', 'log_retention_days', fallback=7)

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    parent_dir_name = os.path.basename(os.path.dirname(os.path.dirname(log_directory)))
    log_file = os.path.join(log_directory, f'{parent_dir_name}.log')

    file_handler = TimedRotatingFileHandler(filename=log_file, when='midnight', backupCount=log_retention_days,
                                            encoding='utf-8')
    file_handler.suffix = "%Y-%m-%d.log"

    checkpoint_log_file = os.path.join(log_directory, f'{parent_dir_name}_checkpoint.log')
    checkpoint_handler = TimedRotatingFileHandler(filename=checkpoint_log_file, when='midnight',
                                                  backupCount=log_retention_days, encoding='utf-8')
    checkpoint_handler.suffix = "%Y-%m-%d.log"

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    checkpoint_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    checkpoint_logger = logging.getLogger('checkpoint')
    checkpoint_logger.setLevel(logging.INFO)
    checkpoint_logger.addHandler(checkpoint_handler)
    checkpoint_logger.propagate = False  # ルートロガーに伝播しない

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)  # WARNING以上のみコンソール出力
    root_logger.addHandler(console_handler)

    cleanup_old_logs(log_directory, log_retention_days)


def cleanup_old_logs(log_directory: str, retention_days: int):
    now = datetime.now()
    parent_dir_name = os.path.basename(os.path.dirname(os.path.dirname(log_directory)))

    main_log_file = f'{parent_dir_name}.log'
    checkpoint_log_file = f'{parent_dir_name}_checkpoint.log'

    for filename in os.listdir(log_directory):
        if filename.endswith('.log') and filename not in [main_log_file, checkpoint_log_file]:
            file_path = os.path.join(log_directory, filename)
            try:
                file_modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if now - file_modification_time > timedelta(days=retention_days):
                    os.remove(file_path)
                    logging.info(f"古いログファイルを削除しました: {filename}")
            except OSError as e:
                logging.error(f"ログファイルの削除中にエラーが発生しました {filename}: {str(e)}")


def setup_debug_logging():
    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(logging.DEBUG)

    debug_handler = logging.FileHandler('debug.log', encoding='utf-8')
    debug_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    debug_handler.setFormatter(debug_formatter)
    debug_logger.addHandler(debug_handler)
    debug_logger.propagate = False

    return debug_logger
