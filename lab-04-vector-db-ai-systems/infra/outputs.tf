output "api_base_url" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}

output "ingest_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/ingest"
}

output "search_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/search"
}

output "opensearch_endpoint" {
  value = "https://${aws_opensearch_domain.vector.endpoint}"
}
