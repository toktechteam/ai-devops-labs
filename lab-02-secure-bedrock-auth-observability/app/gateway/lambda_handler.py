import base64
import json
import os
import time
from typing import Any

import boto3

from guardrails import check_guardrails
from logger import JsonLogger, timing_ms
from token_counter import estimate_tokens


MODEL_ID = os.environ.get("MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "512"))
METRICS_NAMESPACE = os.environ.get(
    "METRICS_NAMESPACE", "Lab02/BedrockGateway"
)

logger = JsonLogger()


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


def _invoke_bedrock(prompt: str) -> str:
    client = boto3.client("bedrock-runtime")

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_TOKENS,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ],
            }
        ],
    }

    response = client.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    body = json.loads(response.get("body").read())
    content = body.get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", "")
    return ""


def handler(event: dict, context: Any):
    start = time.time()
    start_ms = int(start * 1000)
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )
    time_epoch = event.get("requestContext", {}).get("timeEpoch")
    api_gateway_to_lambda_ms = None
    if isinstance(time_epoch, (int, float)):
        api_gateway_to_lambda_ms = max(0, start_ms - int(time_epoch))

    body = _parse_body(event)
    prompt = body.get("prompt", "")

    allowed, guardrail_status = check_guardrails(prompt)
    estimated_tokens = estimate_tokens(prompt)

    if not allowed:
        latency_ms = timing_ms(start)
        logger.log(
            request_id=request_id,
            model_id=MODEL_ID,
            prompt_length=len(prompt),
            estimated_tokens=estimated_tokens,
            latency_ms=latency_ms,
            api_gateway_to_lambda_ms=api_gateway_to_lambda_ms,
            guardrail_status=guardrail_status,
        )
        metrics = {
            "EstimatedTokens": (estimated_tokens, "Count"),
            "LatencyMs": (latency_ms, "Milliseconds"),
        }
        if api_gateway_to_lambda_ms is not None:
            metrics["ApiGatewayToLambdaMs"] = (
                api_gateway_to_lambda_ms,
                "Milliseconds",
            )
        logger.log_emf(
            namespace=METRICS_NAMESPACE,
            dimensions={"Service": "llm-gateway", "ModelId": MODEL_ID},
            metrics=metrics,
            fields={
                "request_id": request_id,
                "guardrail_status": guardrail_status,
                "prompt_length": len(prompt),
            },
        )
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "request_id": request_id,
                    "model_id": MODEL_ID,
                    "latency_ms": latency_ms,
                    "estimated_tokens": estimated_tokens,
                    "response": "Blocked by guardrails",
                    "guardrail_status": guardrail_status,
                }
            ),
        }

    response_text = ""
    try:
        model_start = time.time()
        response_text = _invoke_bedrock(prompt)
        model_latency_ms = timing_ms(model_start)
        latency_ms = timing_ms(start)
        non_model_latency_ms = max(0, latency_ms - model_latency_ms)
        logger.log(
            request_id=request_id,
            model_id=MODEL_ID,
            prompt_length=len(prompt),
            estimated_tokens=estimated_tokens,
            latency_ms=latency_ms,
            model_latency_ms=model_latency_ms,
            non_model_latency_ms=non_model_latency_ms,
            api_gateway_to_lambda_ms=api_gateway_to_lambda_ms,
            guardrail_status=guardrail_status,
        )
        metrics = {
            "EstimatedTokens": (estimated_tokens, "Count"),
            "LatencyMs": (latency_ms, "Milliseconds"),
            "ModelLatencyMs": (model_latency_ms, "Milliseconds"),
            "NonModelLatencyMs": (non_model_latency_ms, "Milliseconds"),
        }
        if api_gateway_to_lambda_ms is not None:
            metrics["ApiGatewayToLambdaMs"] = (
                api_gateway_to_lambda_ms,
                "Milliseconds",
            )
        logger.log_emf(
            namespace=METRICS_NAMESPACE,
            dimensions={"Service": "llm-gateway", "ModelId": MODEL_ID},
            metrics=metrics,
            fields={
                "request_id": request_id,
                "guardrail_status": guardrail_status,
                "prompt_length": len(prompt),
            },
        )
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "request_id": request_id,
                    "model_id": MODEL_ID,
                    "latency_ms": latency_ms,
                    "estimated_tokens": estimated_tokens,
                    "response": response_text,
                    "guardrail_status": guardrail_status,
                }
            ),
        }
    except Exception as exc:  # noqa: BLE001
        latency_ms = timing_ms(start)
        model_latency_ms = None
        non_model_latency_ms = None
        if "model_start" in locals():
            model_latency_ms = timing_ms(model_start)
            non_model_latency_ms = max(0, latency_ms - model_latency_ms)
        logger.log(
            request_id=request_id,
            model_id=MODEL_ID,
            prompt_length=len(prompt),
            estimated_tokens=estimated_tokens,
            latency_ms=latency_ms,
            model_latency_ms=model_latency_ms,
            non_model_latency_ms=non_model_latency_ms,
            api_gateway_to_lambda_ms=api_gateway_to_lambda_ms,
            guardrail_status="error",
            error=str(exc),
        )
        metrics = {
            "EstimatedTokens": (estimated_tokens, "Count"),
            "LatencyMs": (latency_ms, "Milliseconds"),
        }
        if model_latency_ms is not None:
            metrics["ModelLatencyMs"] = (model_latency_ms, "Milliseconds")
        if non_model_latency_ms is not None:
            metrics["NonModelLatencyMs"] = (
                non_model_latency_ms,
                "Milliseconds",
            )
        if api_gateway_to_lambda_ms is not None:
            metrics["ApiGatewayToLambdaMs"] = (
                api_gateway_to_lambda_ms,
                "Milliseconds",
            )
        logger.log_emf(
            namespace=METRICS_NAMESPACE,
            dimensions={"Service": "llm-gateway", "ModelId": MODEL_ID},
            metrics=metrics,
            fields={
                "request_id": request_id,
                "guardrail_status": "error",
                "prompt_length": len(prompt),
            },
        )
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "request_id": request_id,
                    "model_id": MODEL_ID,
                    "latency_ms": latency_ms,
                    "estimated_tokens": estimated_tokens,
                    "response": "Internal error",
                    "guardrail_status": "error",
                }
            ),
        }
