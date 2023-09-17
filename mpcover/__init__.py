import logging
from .config import get_config

logging.basicConfig(
    level=get_config().get("logging", "level").upper(),
    format="%(asctime)s %(levelname)8s : %(name)s -> %(message)s",
)
