#!/usr/bin/env bash
set -euo pipefail

SEARCH_URL="${SEARCH_URL:-}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
QUERY="${QUERY:-What is this lab about?}"

if [[ -z "${SEARCH_URL}" ]]; then
  echo "Set SEARCH_URL to the search endpoint (e.g., https://abc.execute-api.us-east-1.amazonaws.com/prod/search)"
  exit 1
fi

if [[ -z "${AUTH_TOKEN}" ]]; then
  echo "Set AUTH_TOKEN to your bearer token"
  exit 1
fi

payload=$(python3 - <<PY
import json
print(json.dumps({"query": "${QUERY}", "top_k": 5}))
PY
)

curl -sS -X POST "${SEARCH_URL}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d "${payload}"
