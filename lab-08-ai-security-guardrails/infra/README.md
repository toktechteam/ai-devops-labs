# Infrastructure

Terraform provisions:
- API Gateway HTTP API
- Lambda Authorizer
- Security Gateway Lambda
- CloudWatch Log Groups

## Quick start
```bash
terraform init
terraform apply -var='region=us-east-1'
```
