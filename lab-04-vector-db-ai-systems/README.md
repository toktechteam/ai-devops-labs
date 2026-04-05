# lab-04-vector-db-ai-systems

Build a vector database layer for AI systems on AWS. This lab adds **embeddings + vector search** so your AI stack can store and retrieve knowledge.

## Architecture
Client / Demo UI
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Ingestion Lambda / Search Lambda
-> Amazon Bedrock (embeddings)
-> OpenSearch (vector index)
-> CloudWatch Logs
-> Response back to client

See `docs/architecture.md` for details.

## Relationship to Lab-03
Lab-04 is **standalone**. Students can:
- **Run Lab-04 directly** without deploying Lab-03 first.
- **Run Lab-03 and Lab-04 side-by-side** by using different `project_name` values.

If Lab-03 infrastructure is destroyed, you can still deploy Lab-04 normally.

## What You Build
- Ingest text -> embeddings -> OpenSearch vector index
- Search queries -> embeddings -> similarity search
- Lightweight UI for ingestion + search

## Security design
- Token authentication via Lambda Authorizer
- OpenSearch access restricted to Lambda roles
- Least-privilege IAM

## Deploy with Terraform
Prereqs:
- AWS credentials configured
- Bedrock embeddings enabled in your region

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
- OpenSearch and Bedrock embeddings incur costs; destroy resources when done.

Outputs:
- `ingest_url` and `search_url`
- `opensearch_endpoint`

## Test the APIs
Ingest sample text:
```bash
export INGEST_URL="$(terraform -chdir=infra output -raw ingest_url)"
export AUTH_TOKEN="my-secret-token"
./tests/ingest_test.sh
```

Search:
```bash
export SEARCH_URL="$(terraform -chdir=infra output -raw search_url)"
export AUTH_TOKEN="my-secret-token"
export QUERY="What does this lab teach?"
./tests/search_test.sh
```

## Local demo UI (ingest + search)
This lightweight local dashboard lets you ingest text and run similarity searches.

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
export SEARCH_API_URL="$(terraform -chdir=infra output -raw search_url)"
export AUTH_TOKEN="my-secret-token"

python app.py
```

Open `http://localhost:8080`.

UI steps (using `docs/sample.txt`):
1. Ingest: paste the contents of `docs/sample.txt` into the text box (or upload it), set `doc_id` to `sample-doc`, then click **Ingest**.
2. Search: try queries that match the sample content, for example `vector data layer`, `similarity search`, `Bedrock embeddings`, `OpenSearch vector index`, `retrieval-augmented generation`.

## API formats

### POST /ingest
```json
{
  "doc_id": "sample-doc",
  "text": "...",
  "chunk_size": 800,
  "chunk_overlap": 100
}
```

### POST /search
```json
{
  "query": "What is vector search?",
  "top_k": 5
}
```

## Observability
- Lambda logs:
  - `/aws/lambda/lab-04-vector-db-ai-systems-ingest`
  - `/aws/lambda/lab-04-vector-db-ai-systems-search`
  - `/aws/lambda/lab-04-vector-db-ai-systems-authorizer`
- API access logs:
  - `/aws/apigateway/lab-04-vector-db-ai-systems-api`

## Sample data
- Sample document: `docs/sample.txt`

## Clean up
```bash
cd infra
terraform destroy
```
