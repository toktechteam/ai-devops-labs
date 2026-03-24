from typing import Tuple

BLOCKED_KEYWORDS = [
    "password",
    "secret",
    "access key",
    "private key",
]


def check_prompt(prompt: str) -> Tuple[bool, str]:
    lowered = prompt.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in lowered:
            return False, f"prompt contains blocked keyword: {keyword}"
    return True, "allowed"
