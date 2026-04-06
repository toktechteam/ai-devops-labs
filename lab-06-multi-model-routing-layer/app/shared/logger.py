import json
from typing import Any


def log(**kwargs: Any) -> None:
    print(json.dumps(kwargs, separators=(",", ":"), default=str))
