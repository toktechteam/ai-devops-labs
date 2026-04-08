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

PROMPT_VALUE="${PROMPT:-List EC2 instances and show health checks}"
MODEL_ID_VALUE="${MODEL_ID:-}"
TEMP_VALUE="${TEMPERATURE:-0.2}"
TOOL_STRATEGY_VALUE="${TOOL_STRATEGY:-auto}"
MAX_TOOL_CALLS_VALUE="${MAX_TOOL_CALLS:-3}"
USE_MODEL_VALUE="${USE_MODEL:-true}"

payload=$(python3 - <<PY
import json
payload = {
  "prompt": "${PROMPT_VALUE}",
  "temperature": float("${TEMP_VALUE}"),
  "tool_strategy": "${TOOL_STRATEGY_VALUE}",
  "max_tool_calls": int("${MAX_TOOL_CALLS_VALUE}"),
  "use_model": "${USE_MODEL_VALUE}".lower() == "true",
}
model_id = "${MODEL_ID_VALUE}".strip()
if model_id:
  payload["model_id"] = model_id
print(json.dumps(payload))
PY
)

curl -sS -X POST "$INVOKE_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload"

echo
