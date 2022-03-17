from typing import Tuple

from .root import Root
from ..controler import Controler


def init(address: Tuple[str, int]):
    """
    Initialize the GUI.

    :arg address: IP address and port for MPD.
    """

    root = Root(address)
    root.mainloop()
