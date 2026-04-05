# Tests

This folder contains API smoke tests for ingest, retrieve, and ask.

## Usage
```bash
export INGEST_URL="https://.../prod/ingest"
export RETRIEVE_URL="https://.../prod/retrieve"
export ASK_URL="https://.../prod/ask"
export AUTH_TOKEN="my-secret-token"

./tests/ingest_test.sh
./tests/retrieve_test.sh
./tests/ask_test.sh
```
