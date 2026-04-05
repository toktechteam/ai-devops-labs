#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${RETRIEVE_URL:-}" ]]; then
  echo "RETRIEVE_URL is required" >&2
  exit 1
fi

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

QUERY_VALUE="${QUERY:-What is RAG?}"

payload=$(python3 - <<PY
import json
query = "${QUERY_VALUE}"
print(json.dumps({
  "query": query,
  "top_k": 5,
  "filters": {"category": "lab"}
}))
PY
)

curl -sS -X POST "$RETRIEVE_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload"

echo
