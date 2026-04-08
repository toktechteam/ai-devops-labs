locals {
  app_dir = "${path.module}/../app"
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
  handler          = "agent_gateway.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.gateway_zip.output_path
  source_code_hash = data.archive_file.gateway_zip.output_base64sha256
  timeout          = 60
  memory_size      = 512

  environment {
    variables = {
      MODEL_ID              = var.model_id
      DEFAULT_TEMPERATURE   = tostring(var.default_temperature)
      DEFAULT_TOOL_STRATEGY = var.default_tool_strategy
      MAX_TOOL_CALLS        = tostring(var.max_tool_calls)
      ENABLE_MODEL          = tostring(var.enable_model)
      DEFAULT_REGION        = var.default_region
    }
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
