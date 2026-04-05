import os

import boto3


BUCKET_NAME = os.environ.get("DOCUMENTS_BUCKET", "")

_client = boto3.client("s3")


def put_document(key: str, content: str) -> None:
    if not BUCKET_NAME:
        return
    _client.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/plain",
    )
