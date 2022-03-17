from typing import Tuple

from .root import Root
from ..controler import Controler


def init(address: Tuple[str, int]):
    root = Root(address)
    root.mainloop()
