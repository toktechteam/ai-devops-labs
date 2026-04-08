# Infrastructure

Terraform provisions:
- API Gateway HTTP API
- Lambda Authorizer
- Agent Gateway Lambda
- CloudWatch Log Groups

## Quick start
```bash
terraform init
terraform apply -var='region=us-east-1'
```
