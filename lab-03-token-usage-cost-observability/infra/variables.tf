variable "project_name" {
  type    = string
  default = "lab-03-token-usage-cost-observability"
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
  default = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "max_tokens" {
  type    = number
  default = 512
}

variable "metrics_namespace" {
  type    = string
  default = "Lab02/BedrockGateway"
}
