#!/usr/bin/env bash
set -euo pipefail

INGEST_URL="${INGEST_URL:-}"
AUTH_TOKEN="${AUTH_TOKEN:-}"

if [[ -z "${INGEST_URL}" ]]; then
  echo "Set INGEST_URL to the ingest endpoint (e.g., https://abc.execute-api.us-east-1.amazonaws.com/prod/ingest)"
  exit 1
fi

if [[ -z "${AUTH_TOKEN}" ]]; then
  echo "Set AUTH_TOKEN to your bearer token"
  exit 1
fi

payload=$(python3 - <<'PY'
import json
from pathlib import Path
text = Path("docs/sample.txt").read_text()
print(json.dumps({"doc_id": "sample-doc", "text": text}))
PY
)

curl -sS -X POST "${INGEST_URL}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d "${payload}"
