locals {
  ingest_app_dir = "${path.module}/../app/ingest"
  search_app_dir = "${path.module}/../app/search"
  authorizer_app_dir = "${path.module}/../app/authorizer"
}

data "archive_file" "ingest_zip" {
  type        = "zip"
  source_dir  = local.ingest_app_dir
  output_path = "${path.module}/ingest.zip"
}

data "archive_file" "search_zip" {
  type        = "zip"
  source_dir  = local.search_app_dir
  output_path = "${path.module}/search.zip"
}

resource "aws_lambda_function" "ingest" {
  function_name    = "${var.project_name}-ingest"
  role             = aws_iam_role.ingest_role.arn
  handler          = "ingest_handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.ingest_zip.output_path
  source_code_hash = data.archive_file.ingest_zip.output_base64sha256
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = "https://${aws_opensearch_domain.vector.endpoint}"
      OPENSEARCH_INDEX    = var.opensearch_index_name
      EMBEDDING_MODEL_ID  = var.embedding_model_id
      EMBEDDING_DIMENSION = tostring(var.embedding_dimension)
      MAX_CHUNKS          = tostring(var.max_chunks)
    }
  }

  depends_on = [aws_cloudwatch_log_group.ingest]
}

resource "aws_lambda_function" "search" {
  function_name    = "${var.project_name}-search"
  role             = aws_iam_role.search_role.arn
  handler          = "search_handler.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.search_zip.output_path
  source_code_hash = data.archive_file.search_zip.output_base64sha256
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = "https://${aws_opensearch_domain.vector.endpoint}"
      OPENSEARCH_INDEX    = var.opensearch_index_name
      EMBEDDING_MODEL_ID  = var.embedding_model_id
      EMBEDDING_DIMENSION = tostring(var.embedding_dimension)
    }
  }

  depends_on = [aws_cloudwatch_log_group.search]
}
