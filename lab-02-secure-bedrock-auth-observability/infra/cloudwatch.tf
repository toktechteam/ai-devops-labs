resource "aws_cloudwatch_log_group" "gateway" {
  name              = "/aws/lambda/${var.project_name}-gateway"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "authorizer" {
  name              = "/aws/lambda/${var.project_name}-authorizer"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/apigateway/${var.project_name}-api"
  retention_in_days = 14
}
