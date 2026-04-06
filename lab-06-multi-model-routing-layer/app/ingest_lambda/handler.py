import os
import time
import uuid
from typing import Any

from shared.bedrock_embeddings import embed_text
from shared.dynamodb_client import get_document, mark_indexed, put_processing
from shared.http_utils import estimate_tokens, json_response, parse_body
from shared.logger import log
from shared.opensearch_client import create_index, index_document, index_exists
from shared.s3_client import put_document
from shared.text_chunker import chunk_text


INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "lab06-docs")
MAX_CHUNKS = int(os.environ.get("MAX_CHUNKS", "40"))
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))


def handler(event: dict, context: Any):
    start = time.time()
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    body = parse_body(event)
    text = (body.get("text") or "").strip()
    doc_id = (body.get("doc_id") or f"doc-{uuid.uuid4().hex[:8]}").strip()
    chunk_size = int(body.get("chunk_size") or 800)
    chunk_overlap = int(body.get("chunk_overlap") or 120)
    metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else None

    if not text:
        return json_response(400, {"error": "text is required"})

    existing = get_document(doc_id)
    if existing and existing.get("status") == "indexed":
        chunk_ids = existing.get("chunk_ids") or []
        return json_response(
            200,
            {
                "doc_id": doc_id,
                "indexed": 0,
                "chunks": chunk_ids,
                "status": "already_indexed",
            },
        )

    s3_key = f"documents/{doc_id}.txt"
    put_processing(doc_id, metadata, s3_key)
    put_document(s3_key, text)

    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        return json_response(400, {"error": "no chunks generated"})

    chunks = chunks[:MAX_CHUNKS]

    first_embedding = embed_text(chunks[0])
    if not first_embedding:
        return json_response(500, {"error": "embedding failed"})

    if not index_exists(INDEX_NAME):
        create_index(INDEX_NAME, EMBEDDING_DIMENSION)

    indexed = 0
    chunk_ids: list[str] = []

    for idx, chunk in enumerate(chunks):
        embedding = first_embedding if idx == 0 else embed_text(chunk)
        if not embedding:
            continue
        chunk_id = f"{doc_id}#{idx}"
        index_document(INDEX_NAME, doc_id, chunk_id, chunk, embedding, metadata)
        indexed += 1
        chunk_ids.append(chunk_id)

    mark_indexed(doc_id, chunk_ids, indexed)

    latency_ms = int((time.time() - start) * 1000)
    log(
        request_id=request_id,
        doc_id=doc_id,
        chunk_count=len(chunks),
        indexed=indexed,
        latency_ms=latency_ms,
        tokens_estimate=estimate_tokens(text),
    )

    return json_response(
        200,
        {
            "doc_id": doc_id,
            "indexed": indexed,
            "chunks": chunk_ids,
        },
    )
