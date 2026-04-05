locals {
  table_base = replace(lower(var.project_name), "/[^a-z0-9-]/", "-")
  table_name = var.dynamodb_table_name != "" ? var.dynamodb_table_name : "${local.table_base}-docs"
}

resource "aws_dynamodb_table" "documents" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "doc_id"

  attribute {
    name = "doc_id"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.rag.arn
  }
}
