# Mermaid Flow

```mermaid
flowchart LR
  A[Client / TheOpsKart UI] --> B[API Gateway HTTP API]
  B --> C[Lambda Authorizer]
  C --> D[Agent Gateway Lambda]
  D --> E[Plan + Intent]
  E --> F[Tool 1: EC2 Inventory]
  F --> G[Tool 2: EC2 Health]
  G --> H[Tool 3: Ticket / Runbook]
  D --> I[Bedrock Model (optional)]
  D --> J[CloudWatch Logs]
```
