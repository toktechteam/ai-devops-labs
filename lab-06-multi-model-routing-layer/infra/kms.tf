resource "aws_kms_key" "routing" {
  description             = "KMS key for Lab-06 routing storage"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "routing" {
  name          = "alias/${var.project_name}-routing"
  target_key_id = aws_kms_key.routing.key_id
}
