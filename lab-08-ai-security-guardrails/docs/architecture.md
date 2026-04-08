# Architecture

## Overview
This lab deploys a production-grade AI security gateway:

Client
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

## Components
- API Gateway HTTP API exposes `POST /invoke`.
- Lambda Authorizer validates `Authorization: Bearer <token>`.
- Security Gateway Lambda:
  - Validates input size and presence.
  - Detects prompt injection patterns.
  - Evaluates policy rules (strict vs monitor).
  - Calls Bedrock only if allowed.
  - Filters output for sensitive data.
- CloudWatch Logs store structured security decisions.

## Security Pipeline
1) Input Validation
2) Prompt Injection Detection
3) Policy Engine
4) Model Invocation
5) Output Filtering
6) Response Sanitization

## Observability
- Structured logs capture violations, risk score, and redactions.
- Lifecycle timing shows where time is spent.

## Security Principles
- Deny risky prompts in strict mode.
- Allow but flag in monitor mode.
- Sanitize sensitive output before returning to clients.
