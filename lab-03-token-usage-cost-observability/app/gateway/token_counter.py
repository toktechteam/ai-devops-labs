def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return int(len(text) / 4)


def calculate_token_usage(prompt: str, response: str) -> tuple[int, int, int]:
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(response)
    total_tokens = input_tokens + output_tokens
    return input_tokens, output_tokens, total_tokens
