# POC Explainer

## Goal
Prove that a single AI gateway can provide **deep observability** without changing every client.

## What you demonstrate
- **OpenTelemetry tracing** across API Gateway -> Lambda -> Bedrock.
- **Request lifecycle tracking** with stage timing.
- **Model latency breakdown** so you can separate model time from app time.
- **Distributed tracing** via W3C `traceparent`.

## Why it matters
AI systems fail in subtle ways. Without traces, you only see a slow request. With deep monitoring you can pinpoint:
- Was the latency caused by the model or your own code?
- Did the request fail before or after Bedrock?
- How many stages were slow across the request lifecycle?

This lab shows the SRE mindset for AI systems.

## How to run the POC
1. Deploy the infrastructure with Terraform.
2. Use the demo UI or `tests/invoke_test.sh` to send a request.
3. Pass a `traceparent` header to force distributed trace correlation.
4. Inspect CloudWatch logs and the X-Ray/OTel trace viewer.
