import os
from typing import Any

from shared.bedrock_llm import generate_answer
from shared.http_utils import estimate_tokens, json_response, parse_body
from shared.logger import log
from shared.otel_utils import (
    extract_context,
    fallback_trace_ids,
    format_traceparent,
    get_exporter_name,
    get_span_ids,
    get_span_kind_server,
    get_tracer,
    span,
)
from shared.timing import StageTimer


DEFAULT_MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-pro-v1:0")
DEFAULT_TEMPERATURE = float(os.environ.get("DEFAULT_TEMPERATURE", "0.2"))

TRACER = get_tracer()
SPAN_KIND_SERVER = get_span_kind_server()
EXPORTER_NAME = get_exporter_name()


def _normalize_headers(headers: dict | None) -> dict:
    if not headers:
        return {}
    normalized = {}
    for key, value in headers.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized[key.lower()] = value
    return normalized


def _parse_xray_trace_id(header_value: str | None) -> str | None:
    if not header_value or not isinstance(header_value, str):
        return None
    parts = header_value.split(";")
    for part in parts:
        if "Root=" in part:
            return part.split("=", 1)[1].strip()
    return None


def _stage_duration(stages: list[dict], name: str) -> float:
    for stage in stages:
        if stage.get("name") == name:
            return float(stage.get("duration_ms") or 0)
    return 0.0


def handler(event: dict, context: Any):
    request_id = (
        event.get("requestContext", {}).get("requestId")
        or getattr(context, "aws_request_id", "unknown")
    )

    headers = _normalize_headers(event.get("headers"))
    incoming_traceparent = headers.get("traceparent")
    xray_trace_id = _parse_xray_trace_id(headers.get("x-amzn-trace-id"))

    timer = StageTimer()
    trace_ctx = extract_context(headers)

    http_context = event.get("requestContext", {}).get("http", {})
    attributes: dict[str, str] = {}
    if http_context.get("method"):
        attributes["http.method"] = http_context.get("method")
    if http_context.get("path"):
        attributes["http.route"] = http_context.get("path")

    with span(
        TRACER,
        "gateway.request",
        context=trace_ctx,
        kind=SPAN_KIND_SERVER,
        attributes=attributes or None,
    ) as root_span:
        root_span.set_attribute("request.id", request_id)
        root_span.set_attribute("ai.system", "bedrock")

        with span(TRACER, "request.parse"):
            with timer.stage("parse"):
                body = parse_body(event)

        with span(TRACER, "request.validate"):
            with timer.stage("validate"):
                prompt = (body.get("prompt") or "").strip()
                if not prompt:
                    trace_id, span_id = get_span_ids(root_span)
                    if not trace_id or not span_id:
                        trace_id, span_id = fallback_trace_ids(incoming_traceparent)
                    return json_response(
                        400,
                        {
                            "error": "prompt is required",
                            "request_id": request_id,
                            "trace": {
                                "trace_id": trace_id,
                                "span_id": span_id,
                            },
                        },
                    )

                model_id = (body.get("model_id") or "").strip() or DEFAULT_MODEL_ID
                temperature = float(body.get("temperature") or DEFAULT_TEMPERATURE)

        answer = ""
        error_message = None
        with span(TRACER, "bedrock.invoke") as bedrock_span:
            bedrock_span.set_attribute("ai.model.id", model_id)
            with timer.stage("bedrock.invoke"):
                try:
                    answer = generate_answer(prompt, model_id, temperature)
                except Exception as exc:  # noqa: BLE001
                    error_message = str(exc)
                    root_span.record_exception(exc)
                    root_span.set_attribute("error", True)

        with span(TRACER, "response.format"):
            with timer.stage("response.format"):
                pass

    stages = timer.stages
    total_ms = timer.total_ms()
    model_latency_ms = _stage_duration(stages, "bedrock.invoke")
    non_model_latency_ms = max(0.0, total_ms - model_latency_ms)

    trace_id, span_id = get_span_ids(root_span)
    if not trace_id or not span_id:
        trace_id, span_id = fallback_trace_ids(incoming_traceparent)

    traceparent_out = format_traceparent(trace_id, span_id)

    response_payload = {
        "request_id": request_id,
        "trace": {
            "trace_id": trace_id,
            "span_id": span_id,
            "traceparent": traceparent_out,
            "incoming_traceparent": incoming_traceparent,
            "xray_trace_id": xray_trace_id,
            "otel_exporter": EXPORTER_NAME,
        },
        "model_id": model_id,
        "latency_ms": total_ms,
        "model_latency_ms": model_latency_ms,
        "non_model_latency_ms": non_model_latency_ms,
        "lifecycle": stages,
        "metrics": {
            "prompt_chars": len(prompt),
            "estimated_tokens": estimate_tokens(prompt),
        },
        "answer": answer,
    }

    log(
        request_id=request_id,
        trace_id=trace_id,
        span_id=span_id,
        model_id=model_id,
        latency_ms=total_ms,
        model_latency_ms=model_latency_ms,
        non_model_latency_ms=non_model_latency_ms,
        exporter=EXPORTER_NAME,
        stages=stages,
        prompt_chars=len(prompt),
        estimated_tokens=estimate_tokens(prompt),
        error=error_message,
    )

    if error_message:
        response_payload["error"] = error_message
        return json_response(500, response_payload)

    return json_response(200, response_payload)
