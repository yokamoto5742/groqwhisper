import configparser
import os


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.ini')


def load_config() -> configparser.ConfigParser:
    """設定ファイルを読み込み、ConfigParserオブジェクトを返す。"""
    config = configparser.ConfigParser()
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
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


def save_config(config: configparser.ConfigParser) -> None:
    """ConfigParserオブジェクトを設定ファイルに保存する。"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except PermissionError:
        print(f"設定ファイルを書き込む権限がありません: {CONFIG_PATH}")
        raise
    except IOError as e:
        print(f"設定ファイルの保存中にエラーが発生しました: {e}")
        raise
