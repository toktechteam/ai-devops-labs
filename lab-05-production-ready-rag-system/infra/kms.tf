resource "aws_kms_key" "rag" {
  description             = "KMS key for Lab-05 RAG storage"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "rag" {
  name          = "alias/${var.project_name}-rag"
  target_key_id = aws_kms_key.rag.key_id
}
