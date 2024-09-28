import configparser
import os

# プロジェクトのルートディレクトリへの相対パスを取得
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    with open(config_path, 'r', encoding='utf-8') as f:
        config.read_file(f)
    return config


def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    with open(config_path, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
