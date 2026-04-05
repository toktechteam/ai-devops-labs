import base64
import json
import os
import time
import uuid
from typing import Any

from embeddings import embed_text
from logger import log
from opensearch_client import create_index, index_document, index_exists
from text_chunker import chunk_text


INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "lab04-docs")
MAX_CHUNKS = int(os.environ.get("MAX_CHUNKS", "40"))


def _parse_body(event: dict) -> dict:
    body = event.get("body")
    if body is None:
        return {}
    if event.get("isBase64Encoded"):
        try:
            body = base64.b64decode(body).decode("utf-8")
        except Exception:  # noqa: BLE001
            return {}
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}
    if isinstance(body, dict):
        return body
    return {}


def handler(event: dict, context: Any):
    start = time.time()
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    body = _parse_body(event)
    text = (body.get("text") or "").strip()
    doc_id = (body.get("doc_id") or f"doc-{uuid.uuid4().hex[:8]}").strip()
    chunk_size = int(body.get("chunk_size") or 800)
    chunk_overlap = int(body.get("chunk_overlap") or 100)

    if not text:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "text is required"}),
        }

    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "no chunks generated"}),
        }

    chunks = chunks[:MAX_CHUNKS]

    indexed = 0
    first_embedding = embed_text(chunks[0])
    if not first_embedding:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "embedding failed"}),
        }

    if not index_exists(INDEX_NAME):
        create_index(INDEX_NAME, len(first_embedding))

    index_document(INDEX_NAME, doc_id, 0, chunks[0], first_embedding)
    indexed += 1

    for idx, chunk in enumerate(chunks[1:], start=1):
        embedding = embed_text(chunk)
        if not embedding:
            continue
        index_document(INDEX_NAME, doc_id, idx, chunk, embedding)
        indexed += 1

    latency_ms = int((time.time() - start) * 1000)
    log(
        request_id=request_id,
        doc_id=doc_id,
        chunk_count=len(chunks),
        indexed=indexed,
        latency_ms=latency_ms,
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "request_id": request_id,
                "doc_id": doc_id,
                "chunks": len(chunks),
                "indexed": indexed,
                "latency_ms": latency_ms,
            }
        ),
    }
