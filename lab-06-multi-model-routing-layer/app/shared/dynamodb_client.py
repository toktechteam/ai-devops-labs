import os
from datetime import datetime, timezone

import boto3


TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "")

_client = boto3.resource("dynamodb")


def _table():
    return _client.Table(TABLE_NAME)


def get_document(doc_id: str) -> dict | None:
    if not TABLE_NAME:
        return None
    response = _table().get_item(Key={"doc_id": doc_id})
    return response.get("Item")


def put_processing(doc_id: str, metadata: dict | None, s3_key: str) -> None:
    if not TABLE_NAME:
        return
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "doc_id": doc_id,
        "status": "processing",
        "created_at": now,
        "updated_at": now,
        "s3_key": s3_key,
    }
    if metadata:
        item["metadata"] = metadata
    _table().put_item(Item=item)


def mark_indexed(doc_id: str, chunk_ids: list[str], indexed: int) -> None:
    if not TABLE_NAME:
        return
    now = datetime.now(timezone.utc).isoformat()
    _table().update_item(
        Key={"doc_id": doc_id},
        UpdateExpression=(
            "SET #status = :status, updated_at = :updated, chunk_ids = :chunks, #indexed = :indexed"
        ),
        ExpressionAttributeNames={"#status": "status", "#indexed": "indexed"},
        ExpressionAttributeValues={
            ":status": "indexed",
            ":updated": now,
            ":chunks": chunk_ids,
            ":indexed": indexed,
        },
    )
