import json
import logging
import os
from typing import Any

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def get_logger() -> logging.Logger:
    logger = logging.getLogger("secure_bedrock_gateway")
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def log_event(**fields: Any) -> None:
    logger = get_logger()
    logger.info(json.dumps(fields))
