locals {
  app_dir = "${path.module}/../app"
}

data "archive_file" "ingest_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/ingest.zip"
}

data "archive_file" "retrieve_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/retrieve.zip"
}

data "archive_file" "ask_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/ask.zip"
}

data "archive_file" "authorizer_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/authorizer.zip"
}

resource "aws_lambda_function" "ingest" {
  function_name    = "${var.project_name}-ingest"
  role             = aws_iam_role.ingest_role.arn
  handler          = "ingest_lambda.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.ingest_zip.output_path
  source_code_hash = data.archive_file.ingest_zip.output_base64sha256
  timeout          = 60
  memory_size      = 512

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = "https://${aws_opensearch_domain.vector.endpoint}"
      OPENSEARCH_INDEX    = var.opensearch_index_name
      EMBEDDING_MODEL_ID  = var.embedding_model_id
      EMBEDDING_DIMENSION = tostring(var.embedding_dimension)
      MAX_CHUNKS          = tostring(var.max_chunks)
      DOCUMENTS_BUCKET    = aws_s3_bucket.documents.bucket
      DYNAMODB_TABLE      = aws_dynamodb_table.documents.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.ingest]
}

resource "aws_lambda_function" "retrieve" {
  function_name    = "${var.project_name}-retrieve"
  role             = aws_iam_role.retrieve_role.arn
  handler          = "retrieve_lambda.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.retrieve_zip.output_path
  source_code_hash = data.archive_file.retrieve_zip.output_base64sha256
  timeout          = 30
  memory_size      = 512

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = "https://${aws_opensearch_domain.vector.endpoint}"
      OPENSEARCH_INDEX    = var.opensearch_index_name
      EMBEDDING_MODEL_ID  = var.embedding_model_id
      EMBEDDING_DIMENSION = tostring(var.embedding_dimension)
    }
  }

  depends_on = [aws_cloudwatch_log_group.retrieve]
}

resource "aws_lambda_function" "ask" {
  function_name    = "${var.project_name}-ask"
  role             = aws_iam_role.ask_role.arn
  handler          = "ask_lambda.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.ask_zip.output_path
  source_code_hash = data.archive_file.ask_zip.output_base64sha256
  timeout          = 60
  memory_size      = 768

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = "https://${aws_opensearch_domain.vector.endpoint}"
      OPENSEARCH_INDEX    = var.opensearch_index_name
      EMBEDDING_MODEL_ID  = var.embedding_model_id
      EMBEDDING_DIMENSION = tostring(var.embedding_dimension)
      LLM_MODEL_ID        = var.llm_model_id
      DEFAULT_TOP_K        = "5"
    }
  }

  depends_on = [aws_cloudwatch_log_group.ask]
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
