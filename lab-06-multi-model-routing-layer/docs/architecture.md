# Architecture

## Overview
This lab deploys a multi-model routing layer for LLM APIs on AWS:

Client
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Router Lambda
   -> Bedrock Model A (fast)
   -> Bedrock Model B (reasoning)
   -> RAG Path (Embeddings + OpenSearch + LLM)
-> S3 (raw documents)
-> DynamoDB (metadata + ingestion status)
-> CloudWatch Logs + X-Ray
-> Response back to client

## Components
- API Gateway HTTP API exposes `POST /ingest` and `POST /route`.
- Lambda Authorizer validates `Authorization: Bearer <token>` and returns an IAM Allow/Deny policy.
- Ingestion Lambda chunks text, generates embeddings, and stores vectors in OpenSearch while writing metadata to DynamoDB and raw content to S3.
- Router Lambda inspects the request and chooses the best-fit route:
  - Fast model for short or summarization tasks.
  - Reasoning model for deep analysis tasks.
  - RAG path for internal knowledge questions.
  - Fallback model if the primary fails.
- Bedrock provides embeddings + multiple LLMs.
- CloudWatch collects logs; X-Ray traces end-to-end latency.

## Security
- Token authentication is enforced at the API edge.
- Least-privilege IAM permissions allow only required Bedrock, OpenSearch, S3, and DynamoDB actions.
- Storage encryption uses KMS for S3, OpenSearch, and DynamoDB.

## Observability
- Structured logs include route decisions, model IDs, latency, and token estimates.
- API Gateway access logs are enabled on the `/prod` stage.
- X-Ray traces allow debugging of routing vs generation time.
