import os
import time
from typing import Any

from shared.bedrock_embeddings import embed_text
from shared.bedrock_llm import generate_answer
from shared.http_utils import estimate_tokens, json_response, parse_body
from shared.logger import log
from shared.opensearch_client import search_knn


INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "lab05-docs")
DEFAULT_TOP_K = int(os.environ.get("DEFAULT_TOP_K", "5"))


def _build_prompt(question: str, contexts: list[dict]) -> str:
    context_blocks = []
    for item in contexts:
        chunk_id = item.get("chunk_id")
        text = item.get("text") or ""
        context_blocks.append(f"[{chunk_id}] {text}")
    context_text = "\n\n".join(context_blocks)

    return (
        "You are a helpful assistant. Use only the context below to answer the question. "
        "If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\nAnswer:"
    )


def handler(event: dict, context: Any):
    start = time.time()
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    body = parse_body(event)
    question = (body.get("question") or "").strip()
    top_k = int(body.get("top_k") or DEFAULT_TOP_K)
    temperature = float(body.get("temperature") or 0.2)
    model_id = body.get("model_id") if isinstance(body.get("model_id"), str) else None

    if not question:
        return json_response(400, {"error": "question is required"})

    vector = embed_text(question)
    if not vector:
        return json_response(500, {"error": "embedding failed"})

    response = search_knn(INDEX_NAME, vector, top_k)
    hits = response.get("hits", {}).get("hits", [])
    contexts = []
    citations = []
    for hit in hits:
        source = hit.get("_source", {})
        context_item = {
            "doc_id": source.get("doc_id"),
            "chunk_id": source.get("chunk_id"),
            "text": source.get("text"),
            "score": hit.get("_score"),
        }
        contexts.append(context_item)
        citations.append(
            {
                "doc_id": context_item.get("doc_id"),
                "chunk_id": context_item.get("chunk_id"),
                "score": context_item.get("score"),
            }
        )

    prompt = _build_prompt(question, contexts)
    answer = generate_answer(prompt, model_id, temperature)
    if not answer:
        answer = "I don't know based on the provided context."

    latency_ms = int((time.time() - start) * 1000)
    log(
        request_id=request_id,
        question_length=len(question),
        retrieved=len(contexts),
        latency_ms=latency_ms,
        tokens_estimate=estimate_tokens(question),
    )

    return json_response(
        200,
        {
            "answer": answer,
            "citations": citations,
            "retrieved": len(contexts),
        },
    )
