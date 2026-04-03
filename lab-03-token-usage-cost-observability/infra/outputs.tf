output "api_base_url" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}

output "invoke_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/invoke"
}
