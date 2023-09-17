import configparser
import os.path

__DEFAULTS_CONN = {
    "host": "localhost",
    "port": 6600,
}

__DEFAULTS_BIND = {
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
    config.read_dict({"connection": __DEFAULTS_CONN})
    config.read_dict({"binds": __DEFAULTS_BIND})

    # Read user settings from a file.
    config.read(os.path.expanduser(os.path.join("~", ".mpcover.ini")))

    __CONFIG = config

    return config


__all__ = "get_config"
