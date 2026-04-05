# Architecture

## Overview
This lab deploys a vector database layer for AI systems on AWS:

Client
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Ingestion Lambda / Search Lambda
-> Amazon Bedrock (embeddings)
-> OpenSearch (vector index)
-> CloudWatch Logs
-> Response back to client

## Components
- API Gateway HTTP API exposes `POST /ingest` and `POST /search`.
- Lambda Authorizer validates `Authorization: Bearer <token>` and returns an IAM Allow/Deny policy.
- Ingestion Lambda chunks text, generates embeddings, and stores vectors in OpenSearch.
- Search Lambda generates query embeddings and performs similarity search.
- CloudWatch collects Lambda logs and API access logs for observability.

## Security
- Token authentication is enforced at the API edge.
- Least-privilege IAM permissions allow only `bedrock:InvokeModel` and logging actions.
- Access policies restrict OpenSearch to Lambda roles.

## Observability
- Structured JSON logs include ingestion and search metadata.
- API Gateway access logs are enabled on the `/prod` stage.
