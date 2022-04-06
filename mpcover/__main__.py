#!python

import argparse
import logging
import sys
from tkinter import Tk

from .controler import Controler
from .gui import init

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Album cover viewer for MPD.'
    )
    parser.add_argument(
        '-a', '--address',
        metavar='ADDRESS',
        type=str,
        default='127.0.0.1',
        help='MPD server IP address'
    )
    parser.add_argument(
        '-p', '--port',
        metavar='PORT',
        type=int,
        default=6600,
        help='MPD server port'
    )
    parser.add_argument(
        '-s', '--pass',
        metavar='PASSWORD',
        dest='password',
        type=str,
        default=None,
        help='password for auth with the MPD server'
    )

    return parser.parse_args()

def run():
    """
    Entry point. Called when the `mpcover` command is called.
    """

    arguments = parse_arguments()
    address = arguments.address, arguments.port
    init(address, arguments.password)


if __name__ == '__main__':
    run()
