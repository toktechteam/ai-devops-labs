import json
import os
from typing import Any

import boto3

DEFAULT_MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))


class BedrockInvokeError(Exception):
    pass


def _parse_bedrock_response(body_bytes: bytes) -> str:
    data = json.loads(body_bytes.decode("utf-8"))

    if isinstance(data, dict):
        if "content" in data and isinstance(data["content"], list):
            parts = []
            for item in data["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            text = "".join(parts).strip()
            if text:
                return text

        if "completion" in data:
            return str(data.get("completion", "")).strip()

        if "outputText" in data:
            return str(data.get("outputText", "")).strip()

    return json.dumps(data)


def invoke_bedrock(prompt: str, model_id: str) -> str:
    client = boto3.client("bedrock-runtime")

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
    except Exception as exc:
        raise BedrockInvokeError(str(exc)) from exc

    body_bytes: Any = response.get("body")
    if hasattr(body_bytes, "read"):
        body_bytes = body_bytes.read()

    if not isinstance(body_bytes, (bytes, bytearray)):
        raise BedrockInvokeError("Unexpected Bedrock response body")

    return _parse_bedrock_response(body_bytes)
