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
  handler          = "security_gateway.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.gateway_zip.output_path
  source_code_hash = data.archive_file.gateway_zip.output_base64sha256
  timeout          = 60
  memory_size      = 512

  environment {
    variables = {
      MODEL_ID         = var.model_id
      DEFAULT_TEMPERATURE = tostring(var.default_temperature)
      MAX_PROMPT_CHARS = tostring(var.max_prompt_chars)
      POLICY_MODE      = var.policy_mode
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
