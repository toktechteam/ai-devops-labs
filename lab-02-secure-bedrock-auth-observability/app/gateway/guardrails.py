BLOCKED_KEYWORDS = [
    "password",
    "secret",
    "access key",
    "private key",
]


def check_guardrails(prompt: str) -> tuple[bool, str]:
    if not prompt:
        return False, "empty"

    lower_prompt = prompt.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in lower_prompt:
            return False, f"blocked:{keyword}"

    return True, "allowed"
