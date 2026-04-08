#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${INVOKE_URL:-}" ]]; then
  echo "INVOKE_URL is required" >&2
  exit 1
fi

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

PROMPT_VALUE="${PROMPT:-Explain why OpenTelemetry tracing is critical for AI systems}"
MODEL_ID_VALUE="${MODEL_ID:-}"
TEMP_VALUE="${TEMPERATURE:-0.2}"
TRACEPARENT_VALUE="${TRACEPARENT:-}"

payload=$(python3 - <<PY
import json
payload = {
  "prompt": "${PROMPT_VALUE}",
  "temperature": float("${TEMP_VALUE}")
}
model_id = "${MODEL_ID_VALUE}".strip()
if model_id:
  payload["model_id"] = model_id
print(json.dumps(payload))
PY
)

trace_header=()
if [[ -n "${TRACEPARENT_VALUE}" ]]; then
  trace_header=(-H "traceparent: ${TRACEPARENT_VALUE}")
fi

curl -sS -X POST "$INVOKE_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  "${trace_header[@]}" \
  -d "$payload"

echo
