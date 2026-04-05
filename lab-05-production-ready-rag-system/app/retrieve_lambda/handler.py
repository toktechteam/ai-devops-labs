import os
import time
from typing import Any

from shared.bedrock_embeddings import embed_text
from shared.http_utils import estimate_tokens, json_response, parse_body
from shared.logger import log
from shared.opensearch_client import search_knn


INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "lab05-docs")


def handler(event: dict, context: Any):
    start = time.time()
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    body = parse_body(event)
    query = (body.get("query") or "").strip()
    top_k = int(body.get("top_k") or 5)
    filters = body.get("filters") if isinstance(body.get("filters"), dict) else None

    if not query:
        return json_response(400, {"error": "query is required"})

    vector = embed_text(query)
    if not vector:
        return json_response(500, {"error": "embedding failed"})

    response = search_knn(INDEX_NAME, vector, top_k, filters)
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
        tokens_estimate=estimate_tokens(query),
    )

    return json_response(
        200,
        {
            "results": matches,
        },
    )
