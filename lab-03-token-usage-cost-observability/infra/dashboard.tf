resource "aws_cloudwatch_dashboard" "gateway" {
  dashboard_name = "${var.project_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Total Tokens (Sum)"
          view   = "timeSeries"
          region = var.region
          period = 60
          stat   = "Sum"
          metrics = [
            [
              var.metrics_namespace,
              "TotalTokens",
              "Service",
              "llm-gateway",
              "ModelId",
              var.model_id
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Estimated Cost (Sum)"
          view   = "timeSeries"
          region = var.region
          period = 60
          stat   = "Sum"
          metrics = [
            [
              var.metrics_namespace,
              "EstimatedCostUSD",
              "Service",
              "llm-gateway",
              "ModelId",
              var.model_id
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Request Count (Sum)"
          view   = "timeSeries"
          region = var.region
          period = 60
          stat   = "Sum"
          metrics = [
            [
              var.metrics_namespace,
              "RequestCount",
              "Service",
              "llm-gateway",
              "ModelId",
              var.model_id
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Latency (Average)"
          view   = "timeSeries"
          region = var.region
          period = 60
          stat   = "Average"
          metrics = [
            [
              var.metrics_namespace,
              "LatencyMs",
              "Service",
              "llm-gateway",
              "ModelId",
              var.model_id
            ]
          ]
        }
      }
    ]
  })
}
