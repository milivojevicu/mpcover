import configparser
import os.path

__DEFAULTS_CONNECTION = {
    "host": "localhost",
    "port": 6600,
}

__DEFAULTS_LOGGING = {
    "level": "info",
}

__DEFAULTS_STYLE = {
    "padding": 12,
    "background": "#141414",
}

__DEFAULTS_BINDS = {
    "refresh": "r",
}

__CONFIG = None


def get_config():
    """
    Read configuration from a file.
    """

    global __CONFIG

    if __CONFIG is not None:
        return __CONFIG

    config = configparser.ConfigParser()

    # Load default settings.
    config.read_dict({"connection": __DEFAULTS_CONNECTION})
    config.read_dict({"logging": __DEFAULTS_LOGGING})
    config.read_dict({"style": __DEFAULTS_STYLE})
    config.read_dict({"binds": __DEFAULTS_BINDS})

    # Read user settings from a file.
    config.read(os.path.expanduser(os.path.join("~", ".mpcover.ini")))

    __CONFIG = config

    return config


__all__ = "get_config"
