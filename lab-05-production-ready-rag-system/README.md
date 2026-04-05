# lab-05-production-ready-rag-system

Build a production-ready Retrieval-Augmented Generation (RAG) system on AWS. This lab adds **governed ingestion, vector retrieval, grounded generation, and observability** so your AI stack can answer questions with trusted context.

## Architecture
Client / Demo UI
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Ingestion Lambda / Retrieval Lambda / RAG Lambda
-> Amazon Bedrock (embeddings + LLM)
-> OpenSearch (vector index)
-> DynamoDB (metadata + ingestion status)
-> S3 (raw documents)
-> CloudWatch Logs + X-Ray
-> Response back to client

See `docs/architecture.md` for details.

## Relationship to Lab-04
Lab-05 is **standalone**. Students can:
- **Run Lab-05 directly** without deploying Lab-04 first.
- **Run Lab-04 and Lab-05 side-by-side** by using different `project_name` values.

Lab-05 extends the vector search foundation with a production-grade RAG pipeline and safety controls.

## What You Build
- Ingest documents -> chunk + embed -> OpenSearch vector index
- Retrieve top-k context -> build grounded prompt -> Bedrock LLM answer
- Metadata tracking in DynamoDB and raw docs in S3
- Lightweight UI for ingestion, retrieval, and Q&A

## Why This Matters
- **Trustworthy answers**: responses are grounded in retrieved context.
- **Operational safety**: access control, audit logs, and deterministic pipelines.
- **Scale readiness**: storage + indexing are separated from model execution.
- **Cost awareness**: retrieval first, generation second.

## Security design
- Token authentication via Lambda Authorizer
- Least-privilege IAM for Bedrock, OpenSearch, S3, and DynamoDB
- Encrypted storage with KMS keys (S3 + OpenSearch + DynamoDB)

## Deploy with Terraform
Prereqs:
- AWS credentials configured
- Bedrock access enabled in your region

Commands:
```bash
cd infra
terraform init
terraform apply \
  -var='region=us-east-1' \
  -var='authorizer_token=my-secret-token'
```

Notes:
- OpenSearch domain creation can take 10-20 minutes.
- OpenSearch and Bedrock usage incur costs; destroy resources when done.

Outputs:
- `ingest_url`, `retrieve_url`, and `ask_url`
- `opensearch_endpoint`
- `documents_bucket`

## Test the APIs
Ingest sample text:
```bash
export INGEST_URL="$(terraform -chdir=infra output -raw ingest_url)"
export AUTH_TOKEN="my-secret-token"
./tests/ingest_test.sh
```

Retrieve:
```bash
export RETRIEVE_URL="$(terraform -chdir=infra output -raw retrieve_url)"
export AUTH_TOKEN="my-secret-token"
export QUERY="What does this lab teach?"
./tests/retrieve_test.sh
```

Ask (RAG):
```bash
export ASK_URL="$(terraform -chdir=infra output -raw ask_url)"
export AUTH_TOKEN="my-secret-token"
export QUESTION="Explain how the RAG pipeline works"
./tests/ask_test.sh
```

## Local demo UI (ingest + retrieve + ask)
This lightweight local dashboard lets you ingest content, inspect retrieval results, and ask questions.

Prereqs:
- Python 3.11
- API endpoints + auth token

Run locally:
```bash
cd demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export INGEST_API_URL="$(terraform -chdir=infra output -raw ingest_url)"
export RETRIEVE_API_URL="$(terraform -chdir=infra output -raw retrieve_url)"
export ASK_API_URL="$(terraform -chdir=infra output -raw ask_url)"
export AUTH_TOKEN="my-secret-token"

python app.py
```

Open `http://localhost:8080`.

UI steps (using `docs/sample.txt`):
1. Save settings: set `Ingest API URL`, `Retrieve API URL`, `Ask API URL`, and `Auth Token`, then click **Save Settings**.
2. Ingest: set `Document ID` to a new value (example: `sample-doc-002`), paste the contents of `docs/sample.txt`, keep `Chunk Size` 800 and `Chunk Overlap` 120, set `Metadata (JSON)` to `{"source":"manual","category":"lab"}`, then click **Ingest**.
3. Retrieve: set `Query` to `What is RAG?`, `Top K` to 5, `Filters (JSON)` to `{"category":"lab"}`, then click **Retrieve**.
4. Ask: set `Question` to `Explain the RAG pipeline`, `Top K` to 5, `Temperature` to 0.2, `Model ID (optional)` to `amazon.nova-pro-v1:0`, then click **Ask**.

UI steps (using `docs/student_story.txt`):
1. Ingest: set `Document ID` to `incident-k8s-001`, paste the contents of `docs/student_story.txt`, keep `Chunk Size` 800 and `Chunk Overlap` 120, set `Metadata (JSON)` to `{"source":"story","category":"k8s"}`, then click **Ingest**.
2. Retrieve: set `Query` to `Why did the pods enter CrashLoopBackOff?`, `Top K` to 5, `Filters (JSON)` to `{"category":"k8s"}`, then click **Retrieve**.
3. Ask: set `Question` to `What fixed the issue and which command restarted the deployment?`, `Top K` to 5, `Temperature` to 0.2, `Model ID (optional)` to `amazon.nova-pro-v1:0`, then click **Ask**.

## API formats

### POST /ingest
```json
{
  "doc_id": "sample-doc",
  "text": "...",
  "chunk_size": 800,
  "chunk_overlap": 120,
  "metadata": {
    "source": "manual",
    "category": "lab"
  }
}
```

### POST /retrieve
```json
{
  "query": "What is RAG?",
  "top_k": 5,
  "filters": {
    "category": "lab"
  }
}
```

### POST /ask
```json
{
  "question": "Explain the RAG pipeline",
  "top_k": 5,
  "temperature": 0.2,
  "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
}
```

## Observability
- Lambda logs:
  - `/aws/lambda/lab-05-production-ready-rag-system-ingest`
  - `/aws/lambda/lab-05-production-ready-rag-system-retrieve`
  - `/aws/lambda/lab-05-production-ready-rag-system-ask`
  - `/aws/lambda/lab-05-production-ready-rag-system-authorizer`
- API access logs:
  - `/aws/apigateway/lab-05-production-ready-rag-system-api`

## Sample data
- Sample document: `docs/sample.txt`

## Clean up
```bash
cd infra
terraform destroy
```
