data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "gateway_role" {
  name               = "${var.project_name}-gateway-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role" "authorizer_role" {
  name               = "${var.project_name}-authorizer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_policy" "gateway_policy" {
  name = "${var.project_name}-gateway-policy"
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

resource "aws_iam_role_policy_attachment" "gateway_attach" {
  role       = aws_iam_role.gateway_role.name
  policy_arn = aws_iam_policy.gateway_policy.arn
}

resource "aws_iam_role_policy_attachment" "authorizer_attach" {
  role       = aws_iam_role.authorizer_role.name
  policy_arn = aws_iam_policy.authorizer_policy.arn
}
