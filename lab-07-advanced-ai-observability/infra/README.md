# Infrastructure

Terraform in this folder provisions:
- API Gateway HTTP API
- Lambda Authorizer
- Observability Gateway Lambda
- CloudWatch Log Groups

## Quick start
```bash
terraform init
terraform apply -var='region=us-east-1'
```

## Optional OpenTelemetry
If you attach an ADOT Lambda layer, set `otel_layer_arn`:
```bash
terraform apply \
  -var='otel_layer_arn=YOUR_ADOT_LAYER_ARN'
```
