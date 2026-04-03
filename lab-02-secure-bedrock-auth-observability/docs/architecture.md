# Architecture

## Overview
This lab deploys a secure LLM gateway on AWS:

Client
→ API Gateway (HTTP API)
→ Lambda Authorizer (token authentication)
→ LLM Gateway Lambda
→ Amazon Bedrock
→ CloudWatch Logs + Metrics
→ Response back to client

## Components
- API Gateway HTTP API exposes `POST /invoke`.
- Lambda Authorizer validates `Authorization: Bearer <token>` and returns an IAM Allow/Deny policy.
- Gateway Lambda validates input, applies guardrails, estimates tokens, invokes Amazon Bedrock, and returns a structured response.
- CloudWatch collects Lambda logs and API access logs for observability.

## Security
- Token authentication is enforced at the API edge.
- Least-privilege IAM permissions allow only `bedrock:InvokeModel` and logging actions.
- Guardrails block sensitive prompt patterns before reaching the model.

## Observability
- Structured JSON logs include request metadata.
- API Gateway access logs are enabled on the `/prod` stage.
