# lab-08-ai-security-guardrails

Build a production-grade AI security layer with **guardrails, policy enforcement, and output filtering**. This lab upgrades basic validation into an enterprise AI firewall.

## Architecture
Client / TheOpsKart UI
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Security Gateway Lambda
   -> Input Validation
   -> Prompt Injection Detection
   -> Policy Engine
   -> Bedrock Model
   -> Output Filtering
-> CloudWatch Logs
-> Response back to client

See `docs/architecture.md` for details.

## What You Build
- Prompt injection detection
- Sensitive keyword detection
- Policy-based validation (strict vs monitor)
- Output filtering and response sanitization
- Security decision logs with risk scoring

## Why This Matters
- LLMs can be manipulated with prompt injection.
- RAG or internal prompts can leak sensitive data.
- Output filtering prevents unsafe responses from reaching users.

## Security Design
- Token authentication via Lambda Authorizer
- Policy engine denies risky prompts in strict mode
- Sanitized outputs prevent leakage

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

Outputs:
- `invoke_url`

## Test the API
```bash
export INVOKE_URL="$(terraform -chdir=infra output -raw invoke_url)"
export AUTH_TOKEN="my-secret-token"
./tests/invoke_test.sh
```

## API format

### POST /invoke
```json
{
  "prompt": "Explain why guardrails are important",
  "model_id": "amazon.nova-pro-v1:0",
  "temperature": 0.2,
  "policy_mode": "strict",
  "allow_override": false,
  "enable_output_filter": true
}
```

Response (allowed):
```json
{
  "request_id": "...",
  "allowed": true,
  "policy": {
    "mode": "strict",
    "violations": [],
    "risk_score": 0,
    "injection_detected": false,
    "sensitive_detected": false,
    "allow_override": false
  },
  "model_id": "...",
  "latency_ms": 1200,
  "lifecycle": [
    {"name":"parse","start_ms":0.1,"duration_ms":0.8},
    {"name":"input.validate","start_ms":1.0,"duration_ms":0.2},
    {"name":"prompt.injection","start_ms":1.3,"duration_ms":0.1},
    {"name":"sensitive.keyword","start_ms":1.5,"duration_ms":0.1},
    {"name":"policy.evaluate","start_ms":1.7,"duration_ms":0.2},
    {"name":"model.invoke","start_ms":2.0,"duration_ms":1180.0},
    {"name":"output.filter","start_ms":1182.1,"duration_ms":2.0},
    {"name":"response.format","start_ms":1184.3,"duration_ms":0.5}
  ],
  "metrics": {
    "prompt_chars": 40,
    "estimated_tokens": 10,
    "redactions": 0
  },
  "answer": "..."
}
```

Response (blocked):
```json
{
  "request_id": "...",
  "allowed": false,
  "policy": {
    "mode": "strict",
    "violations": ["prompt_injection_detected"],
    "risk_score": 5,
    "injection_detected": true,
    "sensitive_detected": false,
    "allow_override": false
  },
  "error": "Blocked by security policy"
}
```

## Local demo UI
Prereqs:
- Python 3.11
- API endpoint + auth token

Run locally:
```bash
cd demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export INVOKE_API_URL="$(terraform -chdir=infra output -raw invoke_url)"
export AUTH_TOKEN="my-secret-token"

python app.py
```

Open `http://localhost:8080`.

UI steps (using `docs/sample_prompts.txt`):
1. Save settings: set `Invoke API URL`, `Auth Token`, and `Policy Mode`, then click **Save Settings**.
2. Allowed test: paste a safe prompt from `docs/sample_prompts.txt`, keep `Policy Mode` as `strict`, then click **Invoke + Guardrails**.
3. Blocked test: paste a prompt injection sample, keep `Policy Mode` as `strict`, and click **Invoke + Guardrails** to see a blocked decision.
4. Monitor test: switch `Policy Mode` to `monitor`, paste the injection prompt again, then click **Invoke + Guardrails** to see it allowed but flagged.
5. Output filter: toggle **Enable Output Filter** and compare the sanitized `Answer` vs the `raw_answer` (only returned when filtering is off).

## Guardrails behavior (what happens in backend)
The Security Gateway Lambda enforces multi-step guardrails before invoking the model:
- **Input validation**: checks prompt length and required fields.
- **Detection**: runs prompt injection and sensitive keyword checks.
- **Policy evaluation**: combines detections into a risk score and decides allow/block based on `policy_mode` and `allow_override`.
- **Model invoke**: only runs when allowed.
- **Output filtering**: redacts sensitive patterns when enabled.
- **Lifecycle timing**: response includes stage durations so you can see guardrail overhead.

Default inference settings (from environment defaults):
- `model_id`: `amazon.nova-pro-v1:0`
- `temperature`: `0.2`
Default guardrail limits:
- `max_prompt_chars`: `2000`

## Sample prompts
- `docs/sample_prompts.txt`

## Clean up
```bash
cd infra
terraform destroy
```
