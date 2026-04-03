PRICE_PER_1K_TOKENS = 0.00025


def estimate_cost_usd(total_tokens: int) -> float:
    if total_tokens <= 0:
        return 0.0
    return round((total_tokens / 1000) * PRICE_PER_1K_TOKENS, 8)
