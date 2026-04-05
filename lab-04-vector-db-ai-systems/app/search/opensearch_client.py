import json
import os
import urllib.error
import urllib.request

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
SERVICE = "es"
OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "").rstrip("/")


def _signed_request(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    url = f"{OPENSEARCH_ENDPOINT}/{path.lstrip('/')}"
    data = json.dumps(body).encode("utf-8") if body is not None else None

    headers = {"Content-Type": "application/json"}
    credentials = boto3.Session().get_credentials()
    frozen = credentials.get_frozen_credentials()

    aws_request = AWSRequest(method=method, url=url, data=data, headers=headers)
    SigV4Auth(frozen, SERVICE, REGION).add_auth(aws_request)

    req = urllib.request.Request(
        url=url,
        data=data,
        headers=dict(aws_request.headers.items()),
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"error": payload}


def search_knn(index_name: str, vector: list[float], top_k: int) -> dict:
    body = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": vector,
                    "k": top_k
                }
            }
        },
        "_source": ["doc_id", "chunk_id", "text"],
    }
    status, response = _signed_request("POST", f"{index_name}/_search", body)
    if status not in (200, 201):
        raise RuntimeError(f"OpenSearch search failed: {response}")
    return response
