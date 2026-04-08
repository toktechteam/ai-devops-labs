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

PROMPT_VALUE="${PROMPT:-Explain why guardrails are important in AI systems}"
MODEL_ID_VALUE="${MODEL_ID:-}"
TEMP_VALUE="${TEMPERATURE:-0.2}"
POLICY_MODE_VALUE="${POLICY_MODE:-strict}"
ALLOW_OVERRIDE_VALUE="${ALLOW_OVERRIDE:-false}"
OUTPUT_FILTER_VALUE="${OUTPUT_FILTER:-true}"

payload=$(python3 - <<PY
import json
payload = {
  "prompt": "${PROMPT_VALUE}",
  "temperature": float("${TEMP_VALUE}"),
  "policy_mode": "${POLICY_MODE_VALUE}",
  "allow_override": "${ALLOW_OVERRIDE_VALUE}".lower() == "true",
  "enable_output_filter": "${OUTPUT_FILTER_VALUE}".lower() != "false",
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
