# secure-bedrock-gateway

A minimal, production-style AWS LLM gateway using API Gateway + Lambda + Amazon Bedrock + CloudWatch Logs, deployed with Terraform.

**What it does**
- Exposes `POST /invoke`
- Validates and guardrails prompts
- Invokes Amazon Bedrock
- Logs structured JSON for observability

## Architecture
- **API Gateway (HTTP API)**: public endpoint for `POST /invoke`
- **Lambda (Python 3.11)**: input validation, guardrails, Bedrock invocation
- **Amazon Bedrock**: model inference
- **CloudWatch Logs**: structured JSON logs

Guardrails are keyword-based and block prompts containing `password`, `secret`, `access key`, or `private key`.
The sample request format targets Anthropic Claude 3 models. If you switch to a different model family, update `app/bedrock_client.py`.

## Deployment

Prereqs:
- AWS credentials with permissions to create the resources and invoke Bedrock
- Bedrock model access enabled for the target region and model ID
- Terraform >= 1.5

Steps:
1. `cd infra`
2. `terraform init`
3. `terraform apply`

Optional overrides:
- `-var="aws_region=us-east-1"`
- `-var="default_model_id=anthropic.claude-3-haiku-20240307-v1:0"`
- `-var="max_prompt_length=4000"`
- `-var="log_retention_days=14"`

Terraform outputs:
- `api_invoke_url` for `POST /invoke`

## Curl Examples

Success:
```bash
curl -sS -X POST "$(terraform -chdir=infra output -raw api_invoke_url)" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Summarize the benefits of infrastructure as code."}'
```

Blocked (guardrails):
```bash
curl -sS -X POST "$(terraform -chdir=infra output -raw api_invoke_url)" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"My password is 1234, please store it."}'
```

## Testing

You can run the provided script:
```bash
export API_URL="$(terraform -chdir=infra output -raw api_invoke_url)"
./tests/test_requests.sh
```

`jq` is optional for pretty output. If you don’t have it, remove the `| jq .` parts.

## Environment Variables (Lambda)
- `DEFAULT_MODEL_ID` (default: `anthropic.claude-3-haiku-20240307-v1:0`)
- `MAX_PROMPT_LENGTH` (default: `4000`)
- `LOG_LEVEL` (default: `INFO`)

## Estimated Low-Cost Usage
This POC is low-cost for light testing: HTTP API and Lambda are pay-per-request, and Bedrock charges per token. For short prompts and a small number of requests, costs are typically minimal. Always verify pricing for your region and model.

## Cleanup
```bash
terraform -chdir=infra destroy
```

## How this maps to AI platform engineering
This pattern mirrors enterprise AI gateways: centralized policy enforcement, standardized logging, and audited access to model endpoints. It’s a clean foundation for adding auth, quotas, caching, and model routing while keeping the interface stable for application teams.
