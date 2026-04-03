# lab-02-secure-bedrock-auth-observability

A production-style, minimal AI inference gateway on AWS using API Gateway, a Lambda authorizer, a gateway Lambda, Amazon Bedrock, and CloudWatch observability.

## Architecture
Client
→ API Gateway (HTTP API)
→ Lambda Authorizer (token authentication)
→ LLM Gateway Lambda
→ Amazon Bedrock
→ CloudWatch Logs + Metrics
→ Response back to client

See `docs/architecture.md` for details.

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

## CloudWatch logs
- Lambda logs:
  - `/aws/lambda/lab-02-secure-bedrock-auth-observability-gateway`
  - `/aws/lambda/lab-02-secure-bedrock-auth-observability-authorizer`
- API access logs:
  - `/aws/apigateway/lab-02-secure-bedrock-auth-observability-api`

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
- Live metrics cards and sparklines

## Observability mapping
The gateway Lambda emits structured JSON logs and CloudWatch Embedded Metric Format (EMF) metrics.
- Logs include `request_id`, `model_id`, `prompt_length`, `estimated_tokens`, `latency_ms`, and `guardrail_status`.
- EMF metrics emitted by the gateway:
- `EstimatedTokens` (Count)
- `LatencyMs` (Milliseconds)
- `ModelLatencyMs` (Milliseconds) - time spent in the Bedrock call
- `NonModelLatencyMs` (Milliseconds) - time spent in Lambda outside the Bedrock call
- `ApiGatewayToLambdaMs` (Milliseconds) - time from API Gateway receive to Lambda start
- Namespace is configurable via Terraform `metrics_namespace`.

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
  "latency_ms": 4100,
  "estimated_tokens": 120,
  "response": "...",
  "guardrail_status": "allowed"
}
```
