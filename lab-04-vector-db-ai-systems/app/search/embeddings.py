import json
import os

import boto3


MODEL_ID = os.environ.get("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))

_client = boto3.client("bedrock-runtime")


def embed_text(text: str) -> list[float]:
    payload = {"inputText": text}
    if EMBEDDING_DIMENSION:
        payload["dimensions"] = EMBEDDING_DIMENSION

    response = _client.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    body = json.loads(response.get("body").read())
    embedding = body.get("embedding") or body.get("vector")
    if isinstance(embedding, list):
        return embedding
    return []
