import configparser
import logging
import os
import sys
from typing import Any


def get_config_path():
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた実行ファイルの場合
        base_path = sys._MEIPASS
    else:
        # 通常のPythonスクリプトとして実行される場合
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'config.ini')

CONFIG_PATH = get_config_path()


def get_config_value(config: configparser.ConfigParser, section: str, key: str, default: Any) -> Any:
    try:
        value = config[section][key]
        return type(default)(value)
    except (KeyError, ValueError, TypeError):
        return default


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            config.read_file(f)
    except FileNotFoundError:
        print(f"設定ファイルが見つかりません: {CONFIG_PATH}")
        raise
    except PermissionError:
        print(f"設定ファイルを読み取る権限がありません: {CONFIG_PATH}")
        raise
    except configparser.Error as e:
        print(f"設定ファイルの解析中にエラーが発生しました: {e}")
        raise
    return config


def save_config(config: configparser.ConfigParser):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except PermissionError:
        print(f"設定ファイルを書き込む権限がありません: {CONFIG_PATH}")
        raise
    except IOError as e:
        print(f"設定ファイルの保存中にエラーが発生しました: {e}")
        raise


def validate_config(config: configparser.ConfigParser) -> bool:
    """設定ファイルの妥当性を検証"""
    required_sections = ['AUDIO', 'WHISPER', 'CLIPBOARD', 'PATHS']

    for section in required_sections:
        if section not in config:
            logging.error(f"必須セクション '{section}' が設定ファイルにありません")
            return False

    try:
        int(config['AUDIO']['sample_rate'])
        int(config['AUDIO']['channels'])
        int(config['AUDIO']['chunk'])
        float(config['CLIPBOARD']['paste_delay'])
    except (ValueError, KeyError) as e:
        logging.error(f"設定値が無効です: {str(e)}")
        return False

    return True
