#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
REQUESTS="${REQUESTS:-30}"
SLEEP_MS="${SLEEP_MS:-200}"

if [[ -z "${API_URL}" ]]; then
  echo "Set API_URL to the invoke URL (e.g., https://abc.execute-api.us-east-1.amazonaws.com/prod/invoke)"
  exit 1
fi

if [[ -z "${AUTH_TOKEN}" ]]; then
  echo "Set AUTH_TOKEN to your bearer token"
  exit 1
fi

for i in $(seq 1 "${REQUESTS}"); do
  curl -sS -X POST "${API_URL}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -d '{"prompt":"Give me one DevOps tip in 1 sentence."}' \
    >/dev/null
  printf "."
  sleep "0.${SLEEP_MS}"
done

echo
printf "Sent %s requests.\n" "${REQUESTS}"
