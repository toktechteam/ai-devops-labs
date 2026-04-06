#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ROUTE_URL:-}" ]]; then
  echo "ROUTE_URL is required" >&2
  exit 1
fi

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

PROMPT_VALUE="${PROMPT:-Summarize the Opskart incident in 3 bullets}"
TASK_TYPE_VALUE="${TASK_TYPE:-summarize}"
TOP_K_VALUE="${TOP_K:-5}"
TEMP_VALUE="${TEMPERATURE:-0.2}"
FORCE_RAG_VALUE="${FORCE_RAG:-false}"
MODEL_OVERRIDE_VALUE="${MODEL_OVERRIDE:-}"
FILTERS_VALUE="${FILTERS:-}"

payload=$(python3 - <<PY
import json
prompt = "${PROMPT_VALUE}"
task_type = "${TASK_TYPE_VALUE}"
filters_raw = "${FILTERS_VALUE}".strip()
filters = None
if filters_raw:
  try:
    filters = json.loads(filters_raw)
  except json.JSONDecodeError:
    filters = None
payload = {
  "prompt": prompt,
  "task_type": task_type,
  "top_k": int("${TOP_K_VALUE}"),
  "temperature": float("${TEMP_VALUE}"),
  "force_rag": "${FORCE_RAG_VALUE}".lower() == "true",
}
if filters:
  payload["filters"] = filters
if "${MODEL_OVERRIDE_VALUE}":
  payload["model_override"] = "${MODEL_OVERRIDE_VALUE}"
print(json.dumps(payload))
PY
)

curl -sS -X POST "$ROUTE_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload"

echo
