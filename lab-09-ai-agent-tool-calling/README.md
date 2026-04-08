# lab-09-ai-agent-tool-calling

Build an **AI agent with tool calling** on AWS. This lab adds an intelligence layer where the agent plans actions, calls tools, and returns structured results.

## Architecture
Client / TheOpsKart UI
-> API Gateway (HTTP API)
-> Lambda Authorizer (token authentication)
-> Agent Gateway Lambda
   -> Tool 1: EC2 Inventory
   -> Tool 2: EC2 Health
   -> Tool 3: Ticket / Runbook
-> Bedrock Model (optional)
-> CloudWatch Logs
-> Response back to client

See `docs/architecture.md` for details.

## What You Build
- Agent runtime that plans and executes tools
- Tool calling with chained actions (Tool 1 -> Tool 2)
- Structured output from tool results
- Optional model-based summarization
- TheOpsKart UI to visualize tool flow

## Problem We Are Solving
- LLMs can answer questions but **cannot execute actions** by themselves.
- Production workflows require **multiple system calls** in sequence (inventory -> health -> ticket).
- Teams need **deterministic, auditable outputs** instead of free-form text only.
- Manual, copy-paste workflows slow down incident response and increase errors.

## Why We Need This System
- To **connect language** to **real system actions** in a safe, controlled way.
- To **orchestrate tool chains** automatically instead of one-off scripts.
- To produce **structured outputs** that downstream automation can trust.
- To provide **visibility** into each step (plan, tools, results).

## Use Cases
- **Infra visibility**: “List EC2 instances and show health checks.” (Tool 1 -> Tool 2)
- **Incident response**: detect unhealthy instances and open a ticket automatically.
- **Runbook discovery**: search operational guides based on a live prompt.
- **Ops automation**: generate a summary of tool results for on-call handoff.

## Why This Matters
- Real systems must **take action**, not just answer questions.
- Tool calling enables **automation and system interaction**.
- Chained tools mirror real workflows (inventory -> health -> ticket).

## Security design
- Token authentication via Lambda Authorizer
- Least-privilege IAM for Bedrock + logs

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

Outputs:
- `invoke_url`

## Test the API
```bash
export INVOKE_URL="$(terraform -chdir=infra output -raw invoke_url)"
export AUTH_TOKEN="my-secret-token"
./tests/invoke_test.sh
```

Force a tool chain:
```bash
export TOOL_STRATEGY="force_ec2_chain"
export PROMPT="List EC2 instances and show health checks"
./tests/invoke_test.sh
```

## API format

### POST /invoke
```json
{
  "prompt": "List EC2 instances and show health checks",
  "model_id": "amazon.nova-pro-v1:0",
  "temperature": 0.2,
  "tool_strategy": "auto",
  "max_tool_calls": 3,
  "use_model": true
}
```

Response:
```json
{
  "request_id": "...",
  "agent": {
    "intent": "ec2_inventory",
    "plan": ["aws.ec2.list_instances", "aws.ec2.get_health"],
    "tool_calls": [
      {
        "name": "aws.ec2.list_instances",
        "input": {"region": "us-east-1"},
        "output": {"instances": []},
        "duration_ms": 8.2
      }
    ],
    "structured_output": {
      "instances": [],
      "health": {}
    },
    "final_answer": "..."
  },
  "latency_ms": 1180.5,
  "lifecycle": [
    {"name":"parse","start_ms":0.1,"duration_ms":0.8},
    {"name":"plan","start_ms":1.0,"duration_ms":0.3},
    {"name":"tool.aws.ec2.list_instances","start_ms":1.5,"duration_ms":7.0}
  ],
  "metrics": {
    "prompt_chars": 44,
    "estimated_tokens": 11,
    "tool_calls": 2
  }
}
```

Tool strategy options:
- `auto` (default)
- `force_ec2_chain`
- `force_incident_chain`
- `none`

## Local demo UI
Prereqs:
- Python 3.11
- API endpoint + auth token

Run locally:
```bash
cd demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export INVOKE_API_URL="$(terraform -chdir=infra output -raw invoke_url)"
export AUTH_TOKEN="my-secret-token"

python app.py
```

Open `http://localhost:8080`.

UI steps (using `docs/sample_prompts.txt`):
1. Save settings: set `Invoke API URL`, `Auth Token`, and `Tool Strategy`, then click **Save Settings**.
2. Tool chain demo: set `Tool Strategy` to `force_ec2_chain`, paste the EC2 prompt, and click **Run Agent**.
3. Incident demo: set `Tool Strategy` to `force_incident_chain`, paste the incident prompt, and click **Run Agent**.
4. Verify tool flow: the **Tool Flow** panel should show Tool 1 -> Tool 2 (and Tool 3 if incident flow).
5. Toggle **Use Model** to compare pure tool output vs model summarization.

## Agent behavior (what happens in backend)
The Agent Gateway Lambda runs a simple orchestration loop:
- **Plan**: decide intent and tool sequence based on prompt or `tool_strategy`.
- **Execute tools**: each tool runs in order and enriches context for the next tool.
- **Structured output**: tool outputs are returned under `agent.structured_output`.
- **Optional LLM summary**: if `use_model` is true, the model summarizes tool outputs.
- **Demo tooling**: tools return mock data; replace handlers with real AWS SDK calls for production.

Default agent settings (from environment defaults):
- `model_id`: `amazon.nova-pro-v1:0`
- `temperature`: `0.2`
- `default_tool_strategy`: `auto`
- `max_tool_calls`: `3`

## Supported Prompt Patterns
- **EC2 inventory/health**: prompts containing `ec2` or `instance` trigger Tool 1 -> Tool 2.
- **Incident chain**: prompts containing `ec2/instance` plus `incident`, `alert`, or `ticket` trigger Tool 1 -> Tool 2 -> Tool 3.
- **Runbook search**: prompts containing `runbook` or `playbook` trigger runbook lookup.
- **Ticket only**: prompts containing `ticket` or `incident` (without EC2) trigger ticket creation.
- **Direct answer**: everything else returns a response without tools.

## Future Extensions
- **Slack ticketing + alerts**: replace the ticket tool with Slack API calls to post incidents or trigger workflows.
- **Runbooks in S3**: store runbooks in S3 and index them for semantic search, then cite the matched sections.
- **Event-driven agent**: trigger the agent from CloudWatch alarms or webhooks instead of manual prompts.

## Observability
- Lambda logs:
  - `/aws/lambda/lab-09-ai-agent-tool-calling-gateway`
  - `/aws/lambda/lab-09-ai-agent-tool-calling-authorizer`
- API access logs:
  - `/aws/apigateway/lab-09-ai-agent-tool-calling-api`

Quick verification:
```bash
aws logs tail /aws/lambda/lab-09-ai-agent-tool-calling-gateway --since 10m --format short --region us-east-1
```

## Sample prompts
- `docs/sample_prompts.txt`

## Clean up
```bash
cd infra
terraform destroy
```
