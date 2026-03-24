resource "aws_lambda_function" "gateway" {
  function_name = var.project_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_handler.lambda_handler"
  runtime       = "python3.11"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout = var.lambda_timeout
  memory_size = var.lambda_memory

  environment {
    variables = {
      DEFAULT_MODEL_ID  = var.default_model_id
      MAX_PROMPT_LENGTH = var.max_prompt_length
      LOG_LEVEL         = var.log_level
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda_logs]
}
