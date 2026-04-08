# Student Project Summary - Lab-07 Advanced AI Observability

This document explains every UI option in the Advanced AI Observability Studio and how to test it end-to-end. It is written for first-time users.

**Goal of this lab**
You are building an AI gateway that behaves like an SRE-grade monitoring system. Every request is traced, the request lifecycle is timed, and model latency is separated from non-model latency so you can diagnose slowdowns precisely.

**What you learn**
- How trace IDs connect logs, spans, and requests.
- How lifecycle stages explain where time is spent.
- How model latency differs from app latency.
- How to propagate distributed traces with `traceparent`.

## 1) How to test using the UI (first time)

1. **Invoke API URL**
   Paste the API Gateway endpoint ending with `/prod/invoke`.
2. **Auth Token**
   Paste the token value you set in Terraform. The UI adds `Bearer` automatically.
3. **Traceparent (optional)**
   Leave empty for auto-generated trace, or click **Generate Traceparent** to create one.
4. **Prompt**
   Use a simple prompt such as: `Explain why trace context propagation matters in AI systems.`
5. **Model ID**
   Leave blank to use the default model from Lambda (`MODEL_ID`), or set `amazon.nova-pro-v1:0`.
6. **Temperature**
   Keep `0.2` for deterministic output.
7. Click **Save Settings**.
8. Click **Invoke + Trace**.

**Temperature** controls randomness in the model’s output.

Low temperature (like 0.2) → more deterministic, stable, and repeatable answers.
High temperature (like 0.7–1.0) → more creative, diverse, but less consistent answers.
**Why 0.2 here?**
This is an observability lab. We want consistent outputs so you can focus on tracing, latency breakdown, and lifecycle stages without the answer changing each run. 0.2 is low enough to keep the response stable, but not totally rigid.

If you want more creative output, raise it to 0.7 and test again—you’ll see more variation.

**Expected result**
- Status shows **Response ready**.
- **Trace Summary** shows a trace ID and span ID.
- **Lifecycle Stages** appear (parse, validate, bedrock.invoke, response.format).
- **Model Latency** shows total, model, and non-model time.
- **Answer** shows the model response.

## 2) UI Overview (what each option does)

### Top configuration bar
**Invoke API URL**
- The API endpoint of your gateway (`POST /invoke`).
- Used by the UI to send the request to API Gateway.

**Auth Token**
- The shared secret used by the Lambda Authorizer.
- Sent as `Authorization: Bearer <token>`.
- If wrong or missing, you will get `401/403`.

**Traceparent (optional)**
- W3C distributed tracing header.
- Format: `00-<trace-id>-<span-id>-01`.
- When provided, the Lambda uses it as the root of the trace so all services share the same trace.

**Save Settings**
- Stores URL, token, and traceparent in browser local storage.
- This prevents re-typing on refresh.

### Left panel: Invoke Request
**Prompt**
- The input text sent to the model.
- Required field. If empty, the API responds with `prompt is required`.

**Model ID**
- Optional override for which Bedrock model to call.
- If blank, the Lambda uses `MODEL_ID` from environment variables.

**Temperature**
- Controls randomness in the model output.
- Lower values (`0.1-0.3`) are more deterministic.
- Higher values (`0.7-1.0`) are more creative but less consistent.

**Generate Traceparent**
- Creates a new valid `traceparent` value in the UI.
- Useful when you want to test trace propagation without external tooling.

**Send Traceparent (checkbox)**
- If checked, the UI sends the traceparent header.
- If unchecked, the system creates a new trace automatically.

**Invoke + Trace**
- Executes the request and records a full trace plus timing stages.
- The UI then renders the trace summary, stages, latency, and answer.

**Status badge (top-right of panel)**
- `Idle`: No request sent yet.
- `Response ready`: The request succeeded and UI is populated.
- `Error`: Validation failure or backend error.

### Right panel: Trace + Lifecycle
**Trace Summary**
Trace ID: Global identifier for the request (32 hex chars).
Span ID: Identifier for the root span within the trace (16 hex chars).
Exporter: `none` means the OTel layer is not attached, and `xray` or `otlp` means traces are exported to X-Ray or an OTLP backend.

**Lifecycle Stages**
Each card shows stage name, start time, and duration.
`parse`: JSON decoding and input extraction.
`validate`: Checks required fields and normalizes options.
`bedrock.invoke`: The actual model call. Usually the longest stage.
`response.format`: Creates the final response payload for the client.

**Start time**
- The `start` value is measured relative to request start in milliseconds.
- Example: `start 0.06 ms` means this stage began 0.06 ms after request start.

**Duration**
- How long the stage took in milliseconds.
- This is the most important value for performance analysis.

**Model Latency**
- **Total**: Overall request time.
- **Model**: Time spent in `bedrock.invoke`.
- **Non-model**: Everything else (parse + validate + response + overhead).
- This separation tells you whether slowness is from the model or your own code.

**Answer**
- The model's final output.
- Useful to verify the request truly reached Bedrock and returned normally.

**Status badge (top-right of panel)**
- `Waiting`: No trace yet.
- `Trace captured`: Trace data and lifecycle stages are shown.
- `Failed`: Request failed or response returned an error.

## 3) What "Trace" means in this lab
A trace is a timeline of a single request flowing through your system. In this lab:
- The **root span** represents the gateway request.
- Child spans represent stages like parsing, validation, and model invocation.
- The `traceparent` header is what lets you continue the same trace across services.

This gives you production-grade observability without guessing where the time was spent.

## 4) How to interpret the screenshot (example)
From the screenshot:
- `Trace ID` and `Span ID` confirm a trace was created.
- Lifecycle stages show `bedrock.invoke` took ~8362 ms, which dominates total latency.
- `Non-model` latency is ~0.09 ms, meaning the gateway itself is fast and most time is the model.

## 5) Common troubleshooting
**No trace data**
- Ensure you clicked **Invoke + Trace**.
- Verify `Invoke API URL` is correct and reachable.

**Exporter = none**
- The ADOT layer is not attached. Traces still exist in logs but not exported to X-Ray/OTLP.

**401/403 errors**
- Auth token is missing or wrong. Check `authorizer_token` in Terraform.

**High non-model latency**
- Indicates overhead in parsing, validation, or response formatting.
- Check Lambda logs for slow operations or retries.

## 6) Why this matters (SRE perspective)
- **Actionable latency**: You can prove whether the model or your code is slow.
- **Faster RCA**: Trace IDs let you jump from a UI error to the exact log line.
- **Safe scaling**: You can monitor performance across workloads before production rollout.
