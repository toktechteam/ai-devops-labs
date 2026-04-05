import base64
import json
import os
import time
from typing import Any

from embeddings import embed_text
from logger import log
from opensearch_client import search_knn


INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "lab04-docs")


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
    query = (body.get("query") or "").strip()
    top_k = int(body.get("top_k") or 5)

    if not query:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "query is required"}),
        }

    vector = embed_text(query)
    if not vector:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "embedding failed"}),
        }

    response = search_knn(INDEX_NAME, vector, top_k)
    hits = response.get("hits", {}).get("hits", [])
    matches = []
    for hit in hits:
        source = hit.get("_source", {})
        matches.append(
            {
                "doc_id": source.get("doc_id"),
                "chunk_id": source.get("chunk_id"),
                "text": source.get("text"),
                "score": hit.get("_score"),
            }
        )

    latency_ms = int((time.time() - start) * 1000)
    log(
        request_id=request_id,
        query_length=len(query),
        results=len(matches),
        latency_ms=latency_ms,
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "request_id": request_id,
                "query": query,
                "results": matches,
                "latency_ms": latency_ms,
            }
        ),
    }
