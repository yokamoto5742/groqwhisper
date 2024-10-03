import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta


def setup_logging(config):
    log_directory = config.get('Logging', 'log_directory', fallback='logs')
    log_retention_days = config.getint('Logging', 'log_retention_days', fallback=7)

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file = os.path.join(log_directory, 'audio_recorder.log')

    file_handler = TimedRotatingFileHandler(
        log_file,
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

    # 古いログファイルの削除
    cleanup_old_logs(log_directory, log_retention_days)

def cleanup_old_logs(log_directory, retention_days):
    now = datetime.now()
    for filename in os.listdir(log_directory):
        if filename.endswith('.log') and filename != 'audio_recorder.log':
            file_path = os.path.join(log_directory, filename)
            file_modification_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_modification_time > timedelta(days=retention_days):
                os.remove(file_path)
                logging.info(f"古いログファイルを削除しました: {filename}")
