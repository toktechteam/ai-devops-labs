# App Layer

This folder contains the Lambda handlers and shared utilities for Lab-07.

## Folders
- `observability_lambda/` - API handler that emits deep observability signals (traces + lifecycle timing).
- `authorizer/` - Token-based Lambda Authorizer for API Gateway.
- `shared/` - Bedrock client, OpenTelemetry helpers, HTTP utilities, and logging.

## Notes
- The gateway uses OpenTelemetry if the ADOT Lambda layer is attached. Without it, the app still runs and logs timing metrics.
- `shared/otel_utils.py` safely falls back to no-op tracing when OTel packages are not present.
