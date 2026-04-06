def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    size = max(50, chunk_size)
    overlap = max(0, min(overlap, size - 1))
    step = max(1, size - overlap)

    chunks = []
    for start in range(0, len(cleaned), step):
        chunk = cleaned[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks
