variable "project_name" {
  type    = string
  default = "lab-07-advanced-ai-observability"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "authorizer_token" {
  type    = string
  default = "my-secret-token"
}

variable "model_id" {
  type    = string
  default = "amazon.nova-pro-v1:0"
}

variable "default_temperature" {
  type    = number
  default = 0.2
}

variable "otel_layer_arn" {
  type    = string
  default = ""
}

variable "otel_traces_exporter" {
  type    = string
  default = "xray"
}

variable "otel_exporter_otlp_endpoint" {
  type    = string
  default = ""
}

variable "otel_propagators" {
  type    = string
  default = "tracecontext,baggage"
}

variable "log_retention_days" {
  type    = number
  default = 14
}
