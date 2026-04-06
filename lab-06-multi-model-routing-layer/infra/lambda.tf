locals {
  app_dir = "${path.module}/../app"
}

data "archive_file" "ingest_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/ingest.zip"
}

data "archive_file" "router_zip" {
  type        = "zip"
  source_dir  = local.app_dir
  output_path = "${path.module}/router.zip"
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

resource "aws_lambda_function" "router" {
  function_name    = "${var.project_name}-router"
  role             = aws_iam_role.router_role.arn
  handler          = "router_lambda.handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.router_zip.output_path
  source_code_hash = data.archive_file.router_zip.output_base64sha256
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
      FAST_MODEL_ID       = var.fast_model_id
      REASONING_MODEL_ID  = var.reasoning_model_id
      RAG_MODEL_ID        = var.rag_model_id
      FALLBACK_MODEL_ID   = var.fallback_model_id
      DEFAULT_TOP_K       = "5"
    }
  }

  depends_on = [aws_cloudwatch_log_group.router]
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
