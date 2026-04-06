import json
import os
import urllib.error
import urllib.parse
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


def index_exists(index_name: str) -> bool:
    status, _ = _signed_request("GET", index_name)
    if status == 200:
        return True
    if status == 404:
        return False
    raise RuntimeError(f"OpenSearch index check failed: {status}")


def create_index(index_name: str, dimension: int) -> None:
    body = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "dynamic": True,
            "properties": {
                "doc_id": {"type": "keyword"},
                "chunk_id": {"type": "keyword"},
                "text": {"type": "text"},
                "metadata": {"type": "object", "dynamic": True},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dimension,
                },
            },
        },
    }

    status, response = _signed_request("PUT", index_name, body)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to create index: {response}")


def index_document(
    index_name: str,
    doc_id: str,
    chunk_id: str,
    text: str,
    embedding: list[float],
    metadata: dict | None = None,
) -> None:
    body = {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "text": text,
        "embedding": embedding,
    }
    if metadata:
        body["metadata"] = metadata
    safe_id = urllib.parse.quote(chunk_id)
    path = f"{index_name}/_doc/{safe_id}"
    status, response = _signed_request("PUT", path, body)
    if status not in (200, 201):
        raise RuntimeError(f"Failed to index document: {response}")


def search_knn(index_name: str, vector: list[float], top_k: int, filters: dict | None = None) -> dict:
    query: dict = {
        "knn": {
            "embedding": {
                "vector": vector,
                "k": top_k,
            }
        }
    }

    if filters:
        filter_terms = []
        for key, value in filters.items():
            if value is None:
                continue
            filter_terms.append({"term": {f"metadata.{key}.keyword": value}})
        if filter_terms:
            query = {
                "bool": {
                    "must": query,
                    "filter": filter_terms,
                }
            }

    body = {
        "size": top_k,
        "query": query,
        "_source": ["doc_id", "chunk_id", "text", "metadata"],
    }
    status, response = _signed_request("POST", f"{index_name}/_search", body)
    if status not in (200, 201):
        raise RuntimeError(f"OpenSearch search failed: {response}")
    return response
