locals {
  gateway_app_dir = "${path.module}/../app/gateway"
  authorizer_app_dir = "${path.module}/../app/authorizer"
}

data "archive_file" "gateway_zip" {
  type        = "zip"
  source_dir  = local.gateway_app_dir
  output_path = "${path.module}/gateway.zip"
}

resource "aws_lambda_function" "gateway" {
  function_name    = "${var.project_name}-gateway"
  role             = aws_iam_role.gateway_role.arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.gateway_zip.output_path
  source_code_hash = data.archive_file.gateway_zip.output_base64sha256
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      MODEL_ID          = var.model_id
      MAX_TOKENS        = tostring(var.max_tokens)
      METRICS_NAMESPACE = var.metrics_namespace
    }
  }

  depends_on = [aws_cloudwatch_log_group.gateway]
}
