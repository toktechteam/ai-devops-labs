data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  opensearch_base          = replace(lower(var.project_name), "/[^a-z0-9-]/", "-")
  opensearch_base_prefixed = "os-${local.opensearch_base}"
  opensearch_base_trim     = length(local.opensearch_base_prefixed) > 24 ? substr(local.opensearch_base_prefixed, 0, 24) : local.opensearch_base_prefixed
  opensearch_domain_name   = "${trim(local.opensearch_base_trim, "-")}-os"
  final_domain_name        = var.opensearch_domain_name != "" ? var.opensearch_domain_name : local.opensearch_domain_name
}

data "aws_iam_policy_document" "opensearch_access" {
  statement {
    actions = ["es:ESHttp*"]
    principals {
      type        = "AWS"
      identifiers = [
        aws_iam_role.ingest_role.arn,
        aws_iam_role.router_role.arn
      ]
    }
    resources = [
      "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${local.final_domain_name}/*"
    ]
  }
}

resource "aws_opensearch_domain" "vector" {
  domain_name    = local.final_domain_name
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type  = var.opensearch_instance_type
    instance_count = var.opensearch_instance_count
  }

  ebs_options {
    ebs_enabled = true
    volume_size = var.opensearch_volume_size
    volume_type = "gp3"
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  access_policies = data.aws_iam_policy_document.opensearch_access.json
}
