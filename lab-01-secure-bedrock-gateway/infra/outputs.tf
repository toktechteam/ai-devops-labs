output "api_invoke_url" {
  description = "Invoke URL for POST /invoke"
  value       = "${aws_apigatewayv2_api.gateway.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/invoke"
}

output "lambda_role_arn" {
  description = "IAM role ARN used by Lambda"
  value       = aws_iam_role.lambda_role.arn
}
