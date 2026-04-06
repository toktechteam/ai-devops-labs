data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ingest_role" {
  name               = "${var.project_name}-ingest-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role" "router_role" {
  name               = "${var.project_name}-router-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role" "authorizer_role" {
  name               = "${var.project_name}-authorizer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_policy" "lambda_base" {
  name = "${var.project_name}-lambda-base"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "ingest_policy" {
  name = "${var.project_name}-ingest-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["es:ESHttp*"]
        Resource = [
          aws_opensearch_domain.vector.arn,
          "${aws_opensearch_domain.vector.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.documents.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.documents.arn
      },
      {
        Effect = "Allow"
        Action = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.routing.arn
      }
    ]
  })
}

resource "aws_iam_policy" "router_policy" {
  name = "${var.project_name}-router-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["es:ESHttp*"]
        Resource = [
          aws_opensearch_domain.vector.arn,
          "${aws_opensearch_domain.vector.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "authorizer_policy" {
  name = "${var.project_name}-authorizer-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingest_base" {
  role       = aws_iam_role.ingest_role.name
  policy_arn = aws_iam_policy.lambda_base.arn
}

resource "aws_iam_role_policy_attachment" "router_base" {
  role       = aws_iam_role.router_role.name
  policy_arn = aws_iam_policy.lambda_base.arn
}

resource "aws_iam_role_policy_attachment" "ingest_attach" {
  role       = aws_iam_role.ingest_role.name
  policy_arn = aws_iam_policy.ingest_policy.arn
}

resource "aws_iam_role_policy_attachment" "router_attach" {
  role       = aws_iam_role.router_role.name
  policy_arn = aws_iam_policy.router_policy.arn
}

resource "aws_iam_role_policy_attachment" "authorizer_attach" {
  role       = aws_iam_role.authorizer_role.name
  policy_arn = aws_iam_policy.authorizer_policy.arn
}
