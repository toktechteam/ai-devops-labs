resource "aws_cloudwatch_log_group" "ingest" {
  name              = "/aws/lambda/${var.project_name}-ingest"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "retrieve" {
  name              = "/aws/lambda/${var.project_name}-retrieve"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "ask" {
  name              = "/aws/lambda/${var.project_name}-ask"
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
