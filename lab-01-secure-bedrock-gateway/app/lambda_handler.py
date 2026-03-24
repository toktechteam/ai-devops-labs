import base64
import json
import os
import time
from typing import Any, Dict

from bedrock_client import invoke_bedrock
from guardrails import check_prompt
from logger import log_event, get_logger

DEFAULT_MODEL_ID = os.getenv("DEFAULT_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "4000"))

logger = get_logger()


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _get_request_id(event: Dict[str, Any]) -> str:
    ctx = event.get("requestContext", {})
    return ctx.get("requestId") or ctx.get("request_id") or "unknown"


def _parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get("body")
    if body is None:
        raise ValueError("Missing request body")

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8")

    if isinstance(body, str):
        return json.loads(body)

    if isinstance(body, dict):
        return body

    raise ValueError("Invalid request body")


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    start = time.time()
    request_id = _get_request_id(event)
    guardrail_status = "allowed"
    model_id = DEFAULT_MODEL_ID
    prompt_length = 0
    response_length = 0

    try:
        payload = _parse_body(event)
        prompt = payload.get("prompt")
        model_id = payload.get("model_id") or DEFAULT_MODEL_ID

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        prompt = prompt.strip()
        prompt_length = len(prompt)
        if prompt_length > MAX_PROMPT_LENGTH:
            raise ValueError(f"prompt exceeds max length of {MAX_PROMPT_LENGTH}")

        allowed, reason = check_prompt(prompt)
        if not allowed:
            guardrail_status = "blocked"
            latency_ms = int((time.time() - start) * 1000)
            log_event(
                request_id=request_id,
                model_id=model_id,
                prompt_length_chars=prompt_length,
                response_length_chars=response_length,
                latency_ms=latency_ms,
                guardrail_status=guardrail_status,
                error_type="guardrail_blocked",
            )
            return _response(400, {
                "request_id": request_id,
                "error": reason,
                "guardrail_status": guardrail_status,
            })

        response_text = invoke_bedrock(prompt=prompt, model_id=model_id)
        response_length = len(response_text)

        latency_ms = int((time.time() - start) * 1000)
        log_event(
            request_id=request_id,
            model_id=model_id,
            prompt_length_chars=prompt_length,
            response_length_chars=response_length,
            latency_ms=latency_ms,
            guardrail_status=guardrail_status,
        )

        return _response(200, {
            "request_id": request_id,
            "model_id": model_id,
            "latency_ms": latency_ms,
            "response": response_text,
            "guardrail_status": guardrail_status,
        })

    except ValueError as exc:
        latency_ms = int((time.time() - start) * 1000)
        log_event(
            request_id=request_id,
            model_id=model_id,
            prompt_length_chars=prompt_length,
            response_length_chars=response_length,
            latency_ms=latency_ms,
            guardrail_status=guardrail_status,
            error_type="invalid_request",
        )
        return _response(400, {
            "request_id": request_id,
            "error": str(exc),
        })
    except Exception as exc:
        latency_ms = int((time.time() - start) * 1000)
        logger.exception("Unhandled error")
        log_event(
            request_id=request_id,
            model_id=model_id,
            prompt_length_chars=prompt_length,
            response_length_chars=response_length,
            latency_ms=latency_ms,
            guardrail_status=guardrail_status,
            error_type="bedrock_invoke_failed",
        )
        return _response(502, {
            "request_id": request_id,
            "error": "Bedrock invocation failed",
            "details": str(exc),
        })
