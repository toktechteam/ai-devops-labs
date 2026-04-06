locals {
  bucket_base = replace(lower(var.project_name), "/[^a-z0-9-]/", "-")
  bucket_trim = length(local.bucket_base) > 40 ? substr(local.bucket_base, 0, 40) : local.bucket_base
  bucket_name = var.documents_bucket_name != "" ? var.documents_bucket_name : "${trim(local.bucket_trim, "-")}-docs"
}

resource "aws_s3_bucket" "documents" {
  bucket = local.bucket_name
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.routing.arn
      sse_algorithm     = "aws:kms"
    }
  }
}
