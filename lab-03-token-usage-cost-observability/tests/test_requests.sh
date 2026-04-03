#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${API_URL:-}" ]]; then
  echo "Set API_URL to the invoke URL (e.g., https://abc.execute-api.us-east-1.amazonaws.com/prod/invoke)"
  exit 1
fi

curl -X POST "${API_URL}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-token" \
  -d '{"prompt":"Explain infrastructure as code"}'
