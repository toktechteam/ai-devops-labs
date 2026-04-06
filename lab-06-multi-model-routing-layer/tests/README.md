# Tests

Bash smoke tests for the ingest and routing APIs.

## Ingest
```bash
export INGEST_URL="https://.../prod/ingest"
export AUTH_TOKEN="my-secret-token"
./ingest_test.sh
```

## Route
```bash
export ROUTE_URL="https://.../prod/route"
export AUTH_TOKEN="my-secret-token"
export PROMPT="Summarize the Opskart incident in 3 bullets"
export TASK_TYPE="summarize"
./route_test.sh
```
