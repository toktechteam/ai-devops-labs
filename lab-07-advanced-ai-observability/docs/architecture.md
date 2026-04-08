# Architecture

## Overview
This lab deploys an AI observability gateway with deep tracing:

Client
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Observability Gateway Lambda
   -> Bedrock Model
-> CloudWatch Logs + X-Ray/OTel
-> Response back to client

## Components
- API Gateway HTTP API exposes `POST /invoke`.
- Lambda Authorizer validates `Authorization: Bearer <token>`.
- Observability Gateway Lambda:
  - Extracts or creates trace context (W3C `traceparent`).
  - Creates OpenTelemetry spans for lifecycle stages.
  - Measures model latency vs non-model latency.
  - Calls Bedrock and returns trace metadata.
- CloudWatch Logs store structured JSON logs.
- X-Ray (or OTLP backend) stores traces.

## Request Lifecycle Stages
- `parse`: body decode + input extraction.
- `validate`: prompt validation + parameter normalization.
- `bedrock.invoke`: model call (primary latency source).
- `response.format`: response construction.

## Observability
- OpenTelemetry spans for each lifecycle stage.
- Trace propagation via W3C `traceparent`.
- Model latency breakdown in response + logs.
- API Gateway access logs for edge latency.

## Security
- Token authentication enforced at the edge.
- Least-privilege IAM for Bedrock invocation and logs.
- X-Ray permissions scoped to trace publishing.
