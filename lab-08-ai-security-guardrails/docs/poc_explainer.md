# POC Explainer

## Goal
Prove that a single AI gateway can enforce enterprise-grade security guardrails before a model is called.

## What you demonstrate
- Input validation and prompt injection detection.
- Policy enforcement (strict vs monitor mode).
- Output filtering and response sanitization.
- Security decisions and violations logged for auditability.

## Why it matters
LLMs introduce new security risks:
- Prompt injection can override policies.
- Sensitive keywords can trigger data leakage.
- Unsafe outputs can expose secrets.

This lab shows how to build an AI firewall layer that stops those issues early.

## How to run the POC
1. Deploy the infrastructure with Terraform.
2. Use the demo UI or `tests/invoke_test.sh` to send a request.
3. Try a normal prompt and a prompt injection example.
4. Observe blocked responses and policy decisions.
