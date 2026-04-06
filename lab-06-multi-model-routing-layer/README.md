# lab-06-multi-model-routing-layer

Build a multi‑model routing layer for LLM APIs on AWS. This lab adds **intelligent routing, model governance, and RAG‑enabled paths** so your AI platform can choose the best model for each request.

## Architecture
Client / Demo UI
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Router Lambda
   -> Bedrock Model A (fast)
   -> Bedrock Model B (reasoning)
   -> RAG Path (Embeddings + OpenSearch + LLM)
-> S3 (raw documents)
-> DynamoDB (metadata + ingestion status)
-> CloudWatch Logs + X-Ray
-> Response back to client

See `docs/architecture.md` for details.

## Relationship to Lab-05
Lab-06 is **standalone**. Students can:
- **Run Lab-06 directly** without deploying Lab-05 first.
- **Run Lab-05 and Lab-06 side-by-side** by using different `project_name` values.

Lab-06 extends the RAG foundation with **multi‑model routing** and policy‑based decisions.

## What You Build
- Router layer that selects the best model based on cost, latency, and task type
- RAG path for internal knowledge queries
- Fallback logic when a primary model fails
- Lightweight UI to test routing decisions

## Why This Matters
- **Cost optimization**: don’t send every request to an expensive model
- **Latency control**: short prompts should use faster models
- **Model specialization**: different tasks → different strengths
- **Resilience**: fallback when a model fails
- **Governance**: centralized routing logic for all apps

## Security design
- Token authentication via Lambda Authorizer
- Least-privilege IAM for Bedrock, OpenSearch, S3, and DynamoDB
- Encrypted storage with KMS keys (S3 + OpenSearch + DynamoDB)

## Deploy with Terraform
Prereqs:
- AWS credentials configured
- Bedrock access enabled in your region

Commands:
```bash
cd infra
terraform init
terraform apply \
  -var='region=us-east-1' \
  -var='authorizer_token=my-secret-token'
```

Notes:
- OpenSearch domain creation can take 10-20 minutes.
- Bedrock and OpenSearch incur costs; destroy resources when done.

Outputs:
- `ingest_url`, `route_url`
- `opensearch_endpoint`
- `documents_bucket`

## Test the APIs
Ingest sample text:
```bash
export INGEST_URL="$(terraform -chdir=infra output -raw ingest_url)"
export AUTH_TOKEN="my-secret-token"
./tests/ingest_test.sh
```

Route request:
```bash
export ROUTE_URL="$(terraform -chdir=infra output -raw route_url)"
export AUTH_TOKEN="my-secret-token"
export PROMPT="Summarize the Opskart incident in 3 bullets"
./tests/route_test.sh
```

## Local demo UI (ingest + route)
This lightweight local dashboard lets you ingest content and test routing decisions.

Prereqs:
- Python 3.11
- API endpoints + auth token

Run locally:
```bash
cd demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export INGEST_API_URL="$(terraform -chdir=infra output -raw ingest_url)"
export ROUTE_API_URL="$(terraform -chdir=infra output -raw route_url)"
export AUTH_TOKEN="my-secret-token"

python app.py
```

Open `http://localhost:8080`.

UI steps (using `docs/sample.txt`):
1. Save settings: set `Ingest API URL`, `Route API URL`, and `Auth Token`, then click **Save Settings**.
2. Ingest: set `Document ID` to `opskart-incident-001`, paste the contents of `docs/sample.txt`, keep `Chunk Size` 800 and `Chunk Overlap` 120, set `Metadata (JSON)` to `{"source":"opskart","category":"internal","service":"checkout-api"}`, then click **Ingest**.
3. Route (fast): set `Task Type` to `summarize`, prompt to `Summarize the Opskart incident in 3 bullets`, then click **Route**.
4. Route (reasoning): set `Task Type` to `reasoning`, prompt to `Analyze why the DB pool change caused latency and propose two mitigations`, then click **Route**.
5. Route (RAG): set `Task Type` to `internal`, prompt to `How do we fix CrashLoopBackOff after a DB config change?`, then click **Route**.

## Routing behavior (what happens in backend)
The Router Lambda inspects the request and picks a path:
- **fast**: short prompts, summarization, rewrite → uses `FAST_MODEL_ID`
- **reasoning**: analysis, architecture, compare → uses `REASONING_MODEL_ID`
- **rag**: internal/runbook/incident requests → uses `RAG_MODEL_ID` and retrieves context from OpenSearch
- **fallback**: if the chosen model fails, the router retries with `FALLBACK_MODEL_ID`

Default model mapping (from Terraform variables):
- `fast_model_id`: `amazon.nova-micro-v1:0`
- `reasoning_model_id`: `amazon.nova-pro-v1:0`
- `rag_model_id`: `amazon.nova-pro-v1:0`
- `fallback_model_id`: `amazon.nova-micro-v1:0`

Where to verify routing decisions:
- Router logs include `route`, `model_id`, `fallback_used`, `retrieved`, and `latency_ms`.
- Check in CloudWatch:
  - `/aws/lambda/lab-06-multi-model-routing-layer-router`
  - `/aws/apigateway/lab-06-multi-model-routing-layer-api`
In the API response, `route` shows the selected path and `retrieved` should be > 0 for RAG requests. RAG responses include `citations` with chunk IDs.

## API formats

### POST /ingest
```json
{
  "doc_id": "opskart-incident-001",
  "text": "...",
  "chunk_size": 800,
  "chunk_overlap": 120,
  "metadata": {
    "source": "opskart",
    "category": "internal",
    "service": "checkout-api"
  }
}
```

### POST /route
```json
{
  "prompt": "Summarize the Opskart incident in 3 bullets",
  "task_type": "summarize",
  "top_k": 5,
  "force_rag": false
}
```

Response:
```json
{
  "route": "fast",
  "model_id": "amazon.nova-micro-v1:0",
  "answer": "...",
  "fallback_used": false,
  "citations": []
}
```

## Observability
- Lambda logs:
  - `/aws/lambda/lab-06-multi-model-routing-layer-ingest`
  - `/aws/lambda/lab-06-multi-model-routing-layer-router`
  - `/aws/lambda/lab-06-multi-model-routing-layer-authorizer`
- API access logs:
  - `/aws/apigateway/lab-06-multi-model-routing-layer-api`

Quick verification (router logs):
```bash
aws logs tail /aws/lambda/lab-06-multi-model-routing-layer-router --since 10m --format short --region us-east-1
```

## Sample data
- Sample document: `docs/sample.txt` (Opskart internal incident + runbook excerpt)

## Clean up
```bash
cd infra
terraform destroy
```
