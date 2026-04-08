output "invoke_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/invoke"
}

output "gateway_function_name" {
  value = aws_lambda_function.gateway.function_name
}
