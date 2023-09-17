#!python

import argparse
import configparser
import logging

from .config import get_config
from .gui import init

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def parse_arguments(config: configparser.ConfigParser) -> argparse.Namespace:
    """
    Parse arguments from the command line.

    :arg config: Configuration object read from a file. Used to set default values.
        Values from the command line override the values from the config file.

    :return: `argparse.Namespace` object with the parsed arguments.
    """

    parser = argparse.ArgumentParser(
        description="Album cover viewer for MPD.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-a",
        "--address",
        metavar="ADDRESS",
        type=str,
        default=config.get("connection", "host"),
        help="MPD server IP address",
    )

    parser.add_argument(
        "-p",
        "--port",
        metavar="PORT",
        type=int,
        default=config.get("connection", "port"),
        help="MPD server port",
    )

    parser.add_argument(
        "-s",
        "--pass",
        metavar="PASSWORD",
        dest="password",
        type=str,
        default=config.get("connection", "password", fallback=None),
        help="password for auth with the MPD server",
    )

    return parser.parse_args()


def run():
    """
    Entry point. Called when the `mpcover` command is called.
    """

    config = get_config()
    arguments = parse_arguments(config)
    address = arguments.address, arguments.port
    init(address, arguments.password)


if __name__ == "__main__":
    run()
