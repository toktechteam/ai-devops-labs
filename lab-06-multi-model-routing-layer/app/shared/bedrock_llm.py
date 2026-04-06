import json
import os

import boto3


DEFAULT_MODEL_ID = os.environ.get("LLM_MODEL_ID", "amazon.nova-pro-v1:0")

_client = boto3.client("bedrock-runtime")


def _invoke_converse(prompt: str, model_id: str, temperature: float) -> str:
    response = _client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "maxTokens": 512,
            "temperature": temperature,
            "topP": 0.9,
        },
    )

    output = response.get("output", {}).get("message", {})
    content = output.get("content") or []
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            text = first.get("text")
            if isinstance(text, str):
                return text.strip()
    return ""


def _invoke_anthropic(prompt: str, model_id: str, temperature: float) -> str:
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    response = _client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    body = json.loads(response.get("body").read())
    content = body.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            text = first.get("text")
            if isinstance(text, str):
                return text.strip()
    if isinstance(body.get("completion"), str):
        return body.get("completion").strip()
    return ""


def generate_answer(prompt: str, model_id: str | None, temperature: float) -> str:
    selected = model_id or DEFAULT_MODEL_ID
    if selected.startswith("amazon.nova-"):
        return _invoke_converse(prompt, selected, temperature)
    if selected.startswith("anthropic."):
        return _invoke_anthropic(prompt, selected, temperature)

    payload = {
        "inputText": f"User: {prompt}\nBot:",
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": temperature,
            "topP": 0.9,
        },
    }

    response = _client.invoke_model(
        modelId=selected,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    body = json.loads(response.get("body").read())
    results = body.get("results")
    if isinstance(results, list) and results:
        text = results[0].get("outputText")
        if isinstance(text, str):
            return text.strip()
    return ""
