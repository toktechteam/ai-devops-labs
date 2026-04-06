import os
import time
from typing import Any

from shared.bedrock_embeddings import embed_text
from shared.bedrock_llm import generate_answer
from shared.http_utils import estimate_tokens, json_response, parse_body
from shared.logger import log
from shared.opensearch_client import search_knn


INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "lab06-docs")
FAST_MODEL_ID = os.environ.get("FAST_MODEL_ID", "amazon.nova-micro-v1:0")
REASONING_MODEL_ID = os.environ.get("REASONING_MODEL_ID", "amazon.nova-pro-v1:0")
RAG_MODEL_ID = os.environ.get("RAG_MODEL_ID", REASONING_MODEL_ID)
FALLBACK_MODEL_ID = os.environ.get("FALLBACK_MODEL_ID", FAST_MODEL_ID)
DEFAULT_TOP_K = int(os.environ.get("DEFAULT_TOP_K", "5"))

FAST_TASKS = {"summarize", "rewrite", "short", "paraphrase"}
REASONING_TASKS = {"reasoning", "analysis", "design", "architecture", "compare"}
INTERNAL_TASKS = {"internal", "runbook", "incident", "postmortem", "sop"}

INTERNAL_KEYWORDS = {
    "runbook",
    "incident",
    "postmortem",
    "sop",
    "internal",
    "crashloopbackoff",
    "kubernetes",
    "db error",
}

REASONING_KEYWORDS = {"analyze", "design", "architecture", "compare", "tradeoff"}


def _detect_route(prompt: str, task_type: str | None, force_rag: bool) -> str:
    text = (prompt or "").lower()
    task = (task_type or "").lower().strip()

    if force_rag or task in INTERNAL_TASKS or any(k in text for k in INTERNAL_KEYWORDS):
        return "rag"
    if task in FAST_TASKS or len(text) < 200:
        return "fast"
    if task in REASONING_TASKS or any(k in text for k in REASONING_KEYWORDS):
        return "reasoning"
    return "reasoning"


def _build_prompt(question: str, contexts: list[dict]) -> str:
    if not contexts:
        return question
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


def _invoke_with_fallback(prompt: str, model_id: str, fallback_id: str, temperature: float) -> tuple[str, str, bool]:
    try:
        answer = generate_answer(prompt, model_id, temperature)
        return answer, model_id, False
    except Exception:  # noqa: BLE001
        if fallback_id and fallback_id != model_id:
            answer = generate_answer(prompt, fallback_id, temperature)
            return answer, fallback_id, True
        raise


def handler(event: dict, context: Any):
    start = time.time()
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    body = parse_body(event)
    prompt = (body.get("prompt") or "").strip()
    task_type = body.get("task_type") if isinstance(body.get("task_type"), str) else None
    force_rag = bool(body.get("force_rag"))
    top_k = int(body.get("top_k") or DEFAULT_TOP_K)
    temperature = float(body.get("temperature") or 0.2)
    filters = body.get("filters") if isinstance(body.get("filters"), dict) else None
    model_override = body.get("model_override") if isinstance(body.get("model_override"), str) else None

    if not prompt:
        return json_response(400, {"error": "prompt is required"})

    route = _detect_route(prompt, task_type, force_rag)

    citations: list[dict] = []
    retrieved = 0

    if route == "rag":
        vector = embed_text(prompt)
        if not vector:
            return json_response(500, {"error": "embedding failed"})
        response = search_knn(INDEX_NAME, vector, top_k, filters)
        hits = response.get("hits", {}).get("hits", [])
        contexts = []
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
        retrieved = len(contexts)
        prompt_to_send = _build_prompt(prompt, contexts)
        model_id = model_override or RAG_MODEL_ID
    elif route == "fast":
        prompt_to_send = prompt
        model_id = model_override or FAST_MODEL_ID
    else:
        prompt_to_send = prompt
        model_id = model_override or REASONING_MODEL_ID

    try:
        answer, final_model_id, fallback_used = _invoke_with_fallback(
            prompt_to_send, model_id, FALLBACK_MODEL_ID, temperature
        )
    except Exception as exc:  # noqa: BLE001
        return json_response(500, {"error": str(exc)})

    latency_ms = int((time.time() - start) * 1000)
    log(
        request_id=request_id,
        route=route,
        model_id=final_model_id,
        fallback_used=fallback_used,
        retrieved=retrieved,
        latency_ms=latency_ms,
        tokens_estimate=estimate_tokens(prompt),
    )

    return json_response(
        200,
        {
            "route": route,
            "model_id": final_model_id,
            "answer": answer,
            "fallback_used": fallback_used,
            "citations": citations,
            "retrieved": retrieved,
        },
    )
