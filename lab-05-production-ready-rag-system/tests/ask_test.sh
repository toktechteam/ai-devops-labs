#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ASK_URL:-}" ]]; then
  echo "ASK_URL is required" >&2
  exit 1
fi

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

QUESTION_VALUE="${QUESTION:-Explain the RAG pipeline}"

payload=$(python3 - <<PY
import json
question = "${QUESTION_VALUE}"
print(json.dumps({
  "question": question,
  "top_k": 5,
  "temperature": 0.2
}))
PY
)

curl -sS -X POST "$ASK_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload"

echo
