#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_FILE="$SCRIPT_DIR/../docs/sample.txt"

if [[ -z "${INGEST_URL:-}" ]]; then
  echo "INGEST_URL is required" >&2
  exit 1
fi

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "AUTH_TOKEN is required" >&2
  exit 1
fi

if [[ ! -f "$SAMPLE_FILE" ]]; then
  echo "Sample file not found: $SAMPLE_FILE" >&2
  exit 1
fi

payload=$(python3 - <<PY
import json
from pathlib import Path
text = Path("$SAMPLE_FILE").read_text()
print(json.dumps({
  "doc_id": "sample-doc",
  "text": text,
  "chunk_size": 800,
  "chunk_overlap": 120,
  "metadata": {"source": "sample", "category": "lab"}
}))
PY
)

curl -sS -X POST "$INGEST_URL" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload"

echo
