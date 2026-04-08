import os
import uuid
from contextlib import contextmanager
from typing import Any


class _NullSpan:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def set_attribute(self, *_args, **_kwargs):
        return None

    def add_event(self, *_args, **_kwargs):
        return None

    def record_exception(self, *_args, **_kwargs):
        return None

    def get_span_context(self):
        return None


class _NullTracer:
    def start_as_current_span(self, *_args, **_kwargs):
        return _NullSpan()


_TRACER = None
_PROPAGATOR = None
_SPAN_KIND_SERVER = None
_EXPORTER_NAME = "none"


def _init_tracer() -> None:
    global _TRACER, _PROPAGATOR, _SPAN_KIND_SERVER, _EXPORTER_NAME
    if _TRACER is not None:
        return

    enable_otel = os.environ.get("ENABLE_OTEL", "true").lower() in ("1", "true", "yes")
    if not enable_otel:
        _TRACER = _NullTracer()
        _EXPORTER_NAME = "disabled"
        return

    try:
        from opentelemetry import trace
        from opentelemetry.propagators.baggage import BaggagePropagator
        from opentelemetry.propagators.composite import CompositePropagator
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.trace import SpanKind
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    except Exception:  # noqa: BLE001
        _TRACER = _NullTracer()
        return

    service_name = os.environ.get("OTEL_SERVICE_NAME") or os.environ.get("SERVICE_NAME") or "lab-07"
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))

    exporter_pref = os.environ.get("OTEL_TRACES_EXPORTER", "").lower().strip()
    exporter = None
    exporter_name = "none"

    if exporter_pref in ("xray", "awsxray", "aws_xray") or not exporter_pref:
        try:
            from opentelemetry.exporter.aws.xray import AWSXRayExporter

            exporter = AWSXRayExporter()
            exporter_name = "xray"
        except Exception:  # noqa: BLE001
            exporter = None

    if exporter is None and exporter_pref in ("otlp", "http/protobuf", "grpc", ""):
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or None
            exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
            exporter_name = "otlp"
        except Exception:  # noqa: BLE001
            exporter = None

    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    _TRACER = trace.get_tracer(service_name)
    _PROPAGATOR = CompositePropagator([TraceContextTextMapPropagator(), BaggagePropagator()])
    _SPAN_KIND_SERVER = SpanKind.SERVER
    _EXPORTER_NAME = exporter_name


def get_tracer():
    _init_tracer()
    return _TRACER or _NullTracer()


def get_propagator():
    _init_tracer()
    return _PROPAGATOR


def get_span_kind_server():
    _init_tracer()
    return _SPAN_KIND_SERVER


def get_exporter_name() -> str:
    _init_tracer()
    return _EXPORTER_NAME


def extract_context(headers: dict) -> Any:
    propagator = get_propagator()
    if propagator is None:
        return None
    return propagator.extract(headers)


def parse_traceparent(traceparent: str | None) -> dict | None:
    if not traceparent or not isinstance(traceparent, str):
        return None
    parts = traceparent.split("-")
    if len(parts) != 4:
        return None
    _, trace_id, span_id, flags = parts
    if len(trace_id) != 32 or len(span_id) != 16:
        return None
    return {"trace_id": trace_id, "span_id": span_id, "flags": flags}


def format_traceparent(trace_id: str, span_id: str, flags: str = "01") -> str:
    return f"00-{trace_id}-{span_id}-{flags}"


def get_span_ids(span: Any) -> tuple[str | None, str | None]:
    if span is None:
        return None, None
    ctx = None
    try:
        ctx = span.get_span_context()
    except Exception:  # noqa: BLE001
        ctx = None
    if not ctx or not getattr(ctx, "is_valid", True):
        return None, None
    trace_id = format(getattr(ctx, "trace_id"), "032x")
    span_id = format(getattr(ctx, "span_id"), "016x")
    return trace_id, span_id


def fallback_trace_ids(traceparent: str | None) -> tuple[str, str]:
    parsed = parse_traceparent(traceparent)
    if parsed:
        return parsed["trace_id"], parsed["span_id"]
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    return trace_id, span_id


@contextmanager
def span(tracer, name: str, context: Any = None, kind: Any = None, attributes: dict | None = None):
    kwargs = {}
    if context is not None:
        kwargs["context"] = context
    if kind is not None:
        kwargs["kind"] = kind
    if attributes:
        kwargs["attributes"] = attributes
    with tracer.start_as_current_span(name, **kwargs) as active_span:
        yield active_span
