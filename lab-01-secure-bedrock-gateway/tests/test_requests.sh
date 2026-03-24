#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${API_URL:-}" ]]; then
  echo "Set API_URL to the Terraform output api_invoke_url before running."
  echo "Example: export API_URL=\"https://abc123.execute-api.us-east-1.amazonaws.com/prod/invoke\""
  exit 1
fi

echo "== Success request =="
curl -sS -X POST "${API_URL}" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Summarize the benefits of infrastructure as code.","model_id":"anthropic.claude-3-haiku-20240307-v1:0"}' \
  | jq .

echo "== Blocked request =="
curl -sS -X POST "${API_URL}" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"My password is 1234, please store it."}' \
  | jq .
