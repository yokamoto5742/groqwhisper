import configparser


def load_config():
    config = configparser.ConfigParser()
    with open('config.ini', 'r', encoding='utf-8') as f:
        config.read_file(f)
    return config


def save_config(config):
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
