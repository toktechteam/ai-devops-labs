import os
from typing import Any

from shared.bedrock_llm import generate_answer
from shared.guardrails import (
    DEFAULT_MAX_CHARS,
    detect_injection,
    detect_sensitive,
    evaluate_policy,
    sanitize_output,
    validate_input,
)
from shared.http_utils import estimate_tokens, json_response, parse_body
from shared.logger import log
from shared.timing import StageTimer


DEFAULT_MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-pro-v1:0")
DEFAULT_TEMPERATURE = float(os.environ.get("DEFAULT_TEMPERATURE", "0.2"))


def handler(event: dict, context: Any):
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    timer = StageTimer()

    with timer.stage("parse"):
        body = parse_body(event)

    prompt = (body.get("prompt") or "").strip()
    model_id = (body.get("model_id") or "").strip() or DEFAULT_MODEL_ID
    temperature = float(body.get("temperature") or DEFAULT_TEMPERATURE)
    policy_mode = (body.get("policy_mode") or "").strip() or None
    allow_override = bool(body.get("allow_override"))
    max_chars = int(body.get("max_prompt_chars") or DEFAULT_MAX_CHARS)
    enable_output_filter = body.get("enable_output_filter")
    if enable_output_filter is None:
        enable_output_filter = True
    enable_output_filter = bool(enable_output_filter)

    with timer.stage("input.validate"):
        valid_input, validation_errors = validate_input(prompt, max_chars)

    with timer.stage("prompt.injection"):
        injection = detect_injection(prompt)

    with timer.stage("sensitive.keyword"):
        sensitive = detect_sensitive(prompt)

    with timer.stage("policy.evaluate"):
        policy = evaluate_policy(prompt, policy_mode, allow_override, max_chars)

    if not policy.allowed:
        total_ms = timer.total_ms()
        response_payload = {
            "request_id": request_id,
            "allowed": False,
            "policy": {
                "mode": policy.policy_mode,
                "violations": policy.violations,
                "risk_score": policy.risk_score,
                "injection_detected": policy.injection_detected,
                "sensitive_detected": policy.sensitive_detected,
                "allow_override": allow_override,
            },
            "metrics": {
                "prompt_chars": policy.prompt_length,
                "estimated_tokens": estimate_tokens(prompt),
            },
            "lifecycle": timer.stages,
            "latency_ms": total_ms,
            "error": "Blocked by security policy",
        }

        log(
            request_id=request_id,
            allowed=False,
            policy_mode=policy.policy_mode,
            violations=policy.violations,
            injection_detected=policy.injection_detected,
            sensitive_detected=policy.sensitive_detected,
            latency_ms=total_ms,
        )

        status_code = 400 if not valid_input else 403
        return json_response(status_code, response_payload)

    answer = ""
    error_message = None
    with timer.stage("model.invoke"):
        try:
            answer = generate_answer(prompt, model_id, temperature)
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)

    filter_result = None
    with timer.stage("output.filter"):
        if enable_output_filter:
            filter_result = sanitize_output(answer)

    with timer.stage("response.format"):
        pass

    total_ms = timer.total_ms()
    output_text = answer
    redactions = 0
    if filter_result:
        output_text = filter_result.sanitized_text
        redactions = filter_result.redactions

    response_payload = {
        "request_id": request_id,
        "allowed": True,
        "policy": {
            "mode": policy.policy_mode,
            "violations": policy.violations,
            "risk_score": policy.risk_score,
            "injection_detected": injection,
            "sensitive_detected": sensitive,
            "allow_override": allow_override,
        },
        "model_id": model_id,
        "latency_ms": total_ms,
        "lifecycle": timer.stages,
        "metrics": {
            "prompt_chars": len(prompt),
            "estimated_tokens": estimate_tokens(prompt),
            "redactions": redactions,
        },
        "answer": output_text,
        "raw_answer": answer if not enable_output_filter else None,
    }

    log(
        request_id=request_id,
        allowed=True,
        policy_mode=policy.policy_mode,
        violations=policy.violations,
        injection_detected=injection,
        sensitive_detected=sensitive,
        latency_ms=total_ms,
        redactions=redactions,
        error=error_message,
    )

    if error_message:
        response_payload["error"] = error_message
        return json_response(500, response_payload)

    return json_response(200, response_payload)
