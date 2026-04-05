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

resource "aws_iam_role" "search_role" {
  name               = "${var.project_name}-search-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role" "authorizer_role" {
  name               = "${var.project_name}-authorizer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_policy" "vector_policy" {
  name = "${var.project_name}-vector-policy"
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
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
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

resource "aws_iam_role_policy_attachment" "ingest_attach" {
  role       = aws_iam_role.ingest_role.name
  policy_arn = aws_iam_policy.vector_policy.arn
}

resource "aws_iam_role_policy_attachment" "search_attach" {
  role       = aws_iam_role.search_role.name
  policy_arn = aws_iam_policy.vector_policy.arn
}

resource "aws_iam_role_policy_attachment" "authorizer_attach" {
  role       = aws_iam_role.authorizer_role.name
  policy_arn = aws_iam_policy.authorizer_policy.arn
}
