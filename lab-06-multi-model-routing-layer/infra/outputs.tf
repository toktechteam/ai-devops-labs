output "api_base_url" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}

output "ingest_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/ingest"
}

output "route_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${aws_apigatewayv2_stage.prod.name}/route"
}

output "opensearch_endpoint" {
  value = "https://${aws_opensearch_domain.vector.endpoint}"
}

output "documents_bucket" {
  value = aws_s3_bucket.documents.bucket
}
