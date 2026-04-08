# lab-07-advanced-ai-observability

Build **advanced AI observability** on AWS: OpenTelemetry tracing, request lifecycle tracking, model latency breakdown, and distributed trace propagation. This is SRE-grade monitoring for AI systems.

## Architecture
Client / TheOpsKart UI
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Observability Gateway Lambda
   -> Bedrock Model
-> CloudWatch Logs + X-Ray/OTel
-> Response back to client

See `docs/architecture.md` for details.

## What You Build
- **OpenTelemetry tracing** for every request
- **Lifecycle stage tracking** (parse, validate, model invoke, response)
- **Model latency breakdown** vs non-model latency
- **Distributed tracing** via W3C `traceparent`
- **TheOpsKart** branded UI for testing

## Why This Matters
- **SRE for AI systems**: you can see where latency originates
- **Faster debugging**: trace IDs connect logs, traces, and requests
- **Real accountability**: separate model time from your own code
- **Production readiness**: reproducible telemetry patterns

## Security design
- Token authentication via Lambda Authorizer
- Least-privilege IAM for Bedrock, CloudWatch Logs, and X-Ray

## Deploy with Terraform
Prereqs:
- AWS credentials configured
- Bedrock access enabled in your region

Commands:
```bash
cd infra
terraform init
terraform plan \
  -var='region=us-east-1' \
  -var='authorizer_token=my-secret-token'

terraform apply \
  -var='region=us-east-1' \
  -var='authorizer_token=my-secret-token'
```

Optional OpenTelemetry layer:
```bash
terraform apply \
  -var='region=us-east-1' \
  -var='authorizer_token=my-secret-token' \
  -var='otel_layer_arn=YOUR_ADOT_LAYER_ARN'
```

## ADOT Lambda Layer (us-east-1, Python)
Use this ARN for us-east-1:
```
arn:aws:lambda:us-east-1:615299751070:layer:AWSOpenTelemetryDistroPython:24
```

How to get `YOUR_ADOT_LAYER_ARN`:
- Open the AWS Distro for OpenTelemetry (ADOT) Lambda docs.
- Scroll to "ADOT Lambda Layer ARNs".
- Choose the Python tab and copy the ARN for your region.

Two ways to enable it:
- Manual (what this lab uses): attach the layer ARN, set `AWS_LAMBDA_EXEC_WRAPPER=/opt/otel-instrument`, and attach the IAM policy `CloudWatchLambdaApplicationSignalsExecutionRolePolicy`.
- Console (no ARN required): Lambda console -> Configuration -> Monitoring and operations tools -> enable Application Signals and Lambda service traces.

Outputs:
- `invoke_url`

## Test the API
```bash
export INVOKE_URL="$(terraform -chdir=infra output -raw invoke_url)"
export AUTH_TOKEN="my-secret-token"
./tests/invoke_test.sh
```

With traceparent:
```bash
export TRACEPARENT="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
./tests/invoke_test.sh
```

## API format

### POST /invoke
```json
{
  "prompt": "Explain distributed tracing in AI systems",
  "model_id": "amazon.nova-pro-v1:0",
  "temperature": 0.2
}
```

Response:
```json
{
  "request_id": "...",
  "trace": {
    "trace_id": "...",
    "span_id": "...",
    "traceparent": "...",
    "otel_exporter": "xray"
  },
  "model_id": "...",
  "latency_ms": 1290.4,
  "model_latency_ms": 1022.7,
  "non_model_latency_ms": 267.7,
  "lifecycle": [
    {"name":"parse","start_ms":0.1,"duration_ms":4.2},
    {"name":"validate","start_ms":4.3,"duration_ms":1.7},
    {"name":"bedrock.invoke","start_ms":6.1,"duration_ms":1022.7},
    {"name":"response.format","start_ms":1029.1,"duration_ms":6.0}
  ],
  "metrics": {
    "prompt_chars": 52,
    "estimated_tokens": 13
  },
  "answer": "..."
}
```

## Observability
- Lambda logs:
  - `/aws/lambda/lab-07-advanced-ai-observability-gateway`
  - `/aws/lambda/lab-07-advanced-ai-observability-authorizer`
- API access logs:
  - `/aws/apigateway/lab-07-advanced-ai-observability-api`

Quick verification:
```bash
aws logs tail /aws/lambda/lab-07-advanced-ai-observability-gateway --since 10m --format short --region us-east-1
```

## Distributed Tracing Notes
- Send a `traceparent` header from the client to correlate traces end-to-end.
- The gateway echoes back `trace.traceparent` so you can chain calls.
- If ADOT is enabled, traces appear in X-Ray or your OTLP backend.

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

UI steps (using `docs/sample_prompt.txt`):
1. Save settings: set `Invoke API URL` and `Auth Token`, optionally paste a `Traceparent`, then click **Save Settings**.
2. Prompt: paste the contents of `docs/sample_prompt.txt` into `Prompt`.
3. Model + temperature: set `Model ID` to `amazon.nova-pro-v1:0` (or leave blank to use the default) and keep `Temperature` at `0.2`.
4. Trace context: click **Generate Traceparent** (optional), keep **Send Traceparent** checked, then click **Invoke + Trace**.
5. Inspect results: confirm `Trace Summary`, `Lifecycle Stages`, and `Model Latency` are populated, and the `Answer` is returned.

## Tracing behavior (what happens in backend)
The Observability Gateway Lambda instruments the request and returns trace metadata:
- **Trace context**: tries to extract W3C `traceparent` from headers; if absent it creates a new trace.
- **Root span**: `gateway.request` is created as a server span and tagged with request metadata.
- **Lifecycle spans**: child spans are created for `request.parse`, `request.validate`, `bedrock.invoke`, and `response.format`.
- **Latency breakdown**: `model_latency_ms` is the `bedrock.invoke` duration, and `non_model_latency_ms` is everything else.
- **Response trace**: the API returns `trace.traceparent` so you can chain downstream calls with the same trace.

Default inference settings (from environment defaults):
- `model_id`: `amazon.nova-pro-v1:0`
- `temperature`: `0.2`

## Sample prompt
- `docs/sample_prompt.txt`

## Clean up
```bash
cd infra
terraform destroy
```
