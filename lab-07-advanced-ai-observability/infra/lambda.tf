locals {
  app_dir      = "${path.module}/../app"
  otel_enabled = length(trimspace(var.otel_layer_arn)) > 0
  otel_env = local.otel_enabled ? {
    AWS_LAMBDA_EXEC_WRAPPER    = "/opt/otel-instrument"
    OTEL_SERVICE_NAME          = var.project_name
    OTEL_TRACES_EXPORTER       = var.otel_traces_exporter
    OTEL_EXPORTER_OTLP_ENDPOINT = var.otel_exporter_otlp_endpoint
    OTEL_PROPAGATORS           = var.otel_propagators
  } : {}
}

data "archive_file" "gateway_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/gateway.zip"
}

data "archive_file" "authorizer_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/authorizer.zip"
}

resource "aws_lambda_function" "gateway" {
  function_name    = "${var.project_name}-gateway"
  role             = aws_iam_role.gateway_role.arn
  handler          = "observability_lambda.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.gateway_zip.output_path
  source_code_hash = data.archive_file.gateway_zip.output_base64sha256
  timeout          = 60
  memory_size      = 512
  layers           = local.otel_enabled ? [var.otel_layer_arn] : []

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = merge(
      {
        MODEL_ID            = var.model_id
        DEFAULT_TEMPERATURE = tostring(var.default_temperature)
      },
      local.otel_env
    )
  }

  depends_on = [aws_cloudwatch_log_group.gateway]
}

resource "aws_lambda_function" "authorizer" {
  function_name    = "${var.project_name}-authorizer"
  role             = aws_iam_role.authorizer_role.arn
  handler          = "authorizer.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.authorizer_zip.output_path
  source_code_hash = data.archive_file.authorizer_zip.output_base64sha256
  timeout          = 5
  memory_size      = 128

  environment {
    variables = {
      AUTH_TOKEN = var.authorizer_token
    }
  }

  depends_on = [aws_cloudwatch_log_group.authorizer]
}
