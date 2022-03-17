#!python

import sys
import logging
from tkinter import Tk

from .controler import Controler
from .gui import init

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run():
    """
    Entry point. Called when the `mpcover` command is called.
    """

    # Default host and port.
    address = '127.0.0.1', 6600

    # Get host and port from commandline arguments.
    if len(sys.argv[1:]) == 2:
        address = (sys.argv[1], int(sys.argv[2]))

    # GUI.
    init(address)


if __name__ == '__main__':
    run()
