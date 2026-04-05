# Architecture

## Overview
This lab deploys a production-ready RAG stack on AWS:

Client
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Ingestion Lambda / Retrieval Lambda / RAG Lambda
-> Amazon Bedrock (embeddings + LLM)
-> OpenSearch (vector index)
-> DynamoDB (metadata + ingestion status)
-> S3 (raw documents)
-> CloudWatch Logs + X-Ray
-> Response back to client

## Components
- API Gateway HTTP API exposes `POST /ingest`, `POST /retrieve`, and `POST /ask`.
- Lambda Authorizer validates `Authorization: Bearer <token>` and returns an IAM Allow/Deny policy.
- Ingestion Lambda chunks text, generates embeddings, and stores vectors in OpenSearch while writing metadata to DynamoDB and raw content to S3.
- Retrieval Lambda generates query embeddings and performs similarity search with optional metadata filters.
- RAG Lambda builds a grounded prompt from retrieved chunks and calls Bedrock for an answer plus citations.
- CloudWatch collects Lambda logs and API access logs. X-Ray traces end-to-end latency.

## Security
- Token authentication is enforced at the API edge.
- Least-privilege IAM permissions allow only required `bedrock:InvokeModel`, `es:ESHttp*`, `s3:*Object`, and `dynamodb:*Item` actions.
- Storage encryption uses KMS for S3, OpenSearch, and DynamoDB.

## Reliability
- DynamoDB tracks ingestion status and chunk metadata for idempotency.
- OpenSearch index mappings are versioned to avoid destructive schema changes.
- All API handlers emit structured JSON logs for auditability.

## Observability
- Structured logs include request IDs, token usage, and vector search latency.
- API Gateway access logs are enabled on the `/prod` stage.
- X-Ray traces allow debugging of retrieval vs generation time.
