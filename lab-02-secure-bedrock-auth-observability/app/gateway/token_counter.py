def estimate_tokens(prompt: str) -> int:
    if not prompt:
        return 0
    return int(len(prompt) / 4)
