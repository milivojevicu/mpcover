from typing import Optional, Tuple

from .root import Root


def init(address: Tuple[str, int], password: Optional[str]):
    """
    Initialize the GUI.

    :arg address: IP address and port for MPD.
    :arg password: Password for auth with the MPD server.
    """

    root = Root(address, password)
    root.mainloop()
