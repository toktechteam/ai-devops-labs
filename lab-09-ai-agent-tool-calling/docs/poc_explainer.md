# POC Explainer

## Goal
Prove that a single AI agent runtime can plan and execute tool calls, then return structured outputs.

## What you demonstrate
- Intent planning + tool selection
- Chained tool execution (Tool 1 -> Tool 2)
- Structured outputs from tools
- Optional LLM summarization on top of tool results
- Full visibility of tool flow in the UI

## Why it matters
Modern AI systems need action:
- Tool calls enable real automation.
- Chains mirror how production workflows actually run.
- Structured outputs make automation auditable.

## How to run the POC
1. Deploy the infrastructure with Terraform.
2. Use the demo UI or `tests/invoke_test.sh` to send a request.
3. Run the EC2 chain prompt and observe Tool 1 -> Tool 2.
4. Switch to the incident prompt to trigger a longer chain.
5. Review tool traces and structured outputs in the UI.
