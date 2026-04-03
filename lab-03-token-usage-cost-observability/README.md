# lab-03-token-usage-cost-observability

A production-style AI inference gateway on AWS with token usage tracking, cost estimation, and CloudWatch dashboards.

## Architecture
Client
→ API Gateway (HTTP API)
→ Lambda Authorizer (token authentication)
→ LLM Gateway Lambda
→ Amazon Bedrock
→ CloudWatch Logs + Metrics
→ Response back to client

See `docs/architecture.md` for details.

## Relationship to Lab‑02
Lab‑03 is **standalone**. Students can:
- **Run Lab‑03 directly** without deploying Lab‑02 first.
- **Run Lab‑02 and Lab‑03 side‑by‑side** by using different `project_name` values to avoid resource name conflicts.

If Lab‑02 infrastructure is destroyed, you can still deploy Lab‑03 normally with:
```bash
cd infra
terraform init
terraform apply
```

## Why the gateway pattern
- Centralizes authentication, validation, and guardrails before LLM calls.
- Provides consistent logging, metrics, and auditing.
- Decouples client concerns from model choice or prompt policies.

## Lambda Authorizer
- Expects: `Authorization: Bearer my-secret-token`
- Returns an IAM policy (Allow/Deny) for API Gateway HTTP API Lambda authorizers.
- Token is configurable via Terraform `authorizer_token`.

## Security design
- Least-privilege IAM for Bedrock invocation and CloudWatch logging.
- Token authentication at the edge.
- Prompt guardrails block sensitive keywords.

## Deploy with Terraform
Prereqs:
- AWS credentials configured for your account.
- Amazon Bedrock enabled in your account/region.

Commands:
```bash
cd infra
terraform init
terraform apply \
  -var='region=us-east-1' \
  -var='authorizer_token=my-secret-token'
```

Outputs:
- `invoke_url` is your API endpoint: `https://.../prod/invoke`

## Test the API
```bash
export API_URL="$(terraform -chdir=infra output -raw invoke_url)"
./tests/test_requests.sh
```

Or use curl directly:
```bash
curl -X POST https://<api-url>/prod/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-token" \
  -d '{"prompt":"Explain infrastructure as code"}'
```

## Load testing (populate metrics)
```bash
export API_URL="$(terraform -chdir=infra output -raw invoke_url)"
export AUTH_TOKEN="my-secret-token"
./tests/load_test.sh
```

## CloudWatch logs
- Lambda logs:
  - `/aws/lambda/lab-03-token-usage-cost-observability-gateway`
  - `/aws/lambda/lab-03-token-usage-cost-observability-authorizer`
- API access logs:
  - `/aws/apigateway/lab-03-token-usage-cost-observability-api`

## Local demo UI (chat + live metrics)
This lightweight local dashboard lets you chat with the API and view live CloudWatch metrics.

Prereqs:
- Python 3.11
- AWS credentials with CloudWatch read access

Run locally:
```bash
cd demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: prefill settings
export API_INVOKE_URL="$(terraform -chdir=infra output -raw invoke_url)"
export AUTH_TOKEN="my-secret-token"
export AWS_REGION="us-east-1"
export METRICS_NAMESPACE="Lab02/BedrockGateway"
export MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"

python app.py
```

Open `http://localhost:8080` and you will see:
- Chat panel (prompt + response)
- Live metrics cards and sparklines (tokens, cost, latency)

## Observability mapping
The gateway Lambda emits structured JSON logs and CloudWatch Embedded Metric Format (EMF) metrics.
- Logs include `request_id`, `model_id`, `prompt_length`, `input_tokens`, `output_tokens`, `total_tokens`, `estimated_cost_usd`, `latency_ms`, and `guardrail_status`.
- EMF metrics emitted by the gateway:
- `InputTokens` (Count)
- `OutputTokens` (Count)
- `TotalTokens` (Count)
- `EstimatedCostUSD` (None) - estimated USD cost for the request
- `RequestCount` (Count)
- `LatencyMs` (Milliseconds)
- `ModelLatencyMs` (Milliseconds) - time spent in the Bedrock call
- `NonModelLatencyMs` (Milliseconds) - time spent in Lambda outside the Bedrock call
- `ApiGatewayToLambdaMs` (Milliseconds) - time from API Gateway receive to Lambda start
- Namespace is configurable via Terraform `metrics_namespace`.

## Token billing and cost estimation
This lab uses a simple, fixed demo price:
- `PRICE_PER_1K_TOKENS = 0.00025`
- `estimated_cost_usd = (total_tokens / 1000) * PRICE_PER_1K_TOKENS`
This is a demo-only cost model, not official Bedrock pricing.

## CloudWatch dashboard
Terraform provisions a CloudWatch dashboard with widgets for:
- Total tokens (Sum)
- Estimated cost (Sum)
- Request count (Sum)
- Latency (Average)
Open it in the CloudWatch Console by name: `lab-03-token-usage-cost-observability-dashboard` (or `<project_name>-dashboard` if you changed the variable).

## AI FinOps concept
Tracking tokens and estimated cost helps teams:
- Monitor AI spend trends over time
- Set budgets and alerts
- Compare model performance vs. cost

## Where zip files are generated
Terraform builds deployment zip files automatically from each Lambda folder.
- Gateway zip: `infra/gateway.zip`
- Authorizer zip: `infra/authorizer.zip`
These are created during `terraform apply` from the `archive_file` data source.
- Gateway source: `app/gateway`
- Authorizer source: `app/authorizer`

## Terraform `app_dir` and token setup
`gateway_app_dir` and `authorizer_app_dir` are Terraform locals that point to each Lambda source folder.
- Defined in `infra/lambda.tf` as `../app/gateway` and `../app/authorizer`
Authorizer token setup:
- Default token is `my-secret-token` in `infra/variables.tf`
- Override at deploy time: `terraform apply -var='authorizer_token=your-token'`

## Response format
```json
{
  "request_id": "...",
  "model_id": "...",
  "latency_ms": 4200,
  "input_tokens": 80,
  "output_tokens": 120,
  "total_tokens": 200,
  "estimated_cost_usd": 0.00005,
  "response": "...",
  "guardrail_status": "allowed"
}
```
