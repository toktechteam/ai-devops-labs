variable "project_name" {
  type    = string
  default = "lab-09-ai-agent-tool-calling"
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

variable "default_tool_strategy" {
  type    = string
  default = "auto"
}

variable "max_tool_calls" {
  type    = number
  default = 3
}

variable "enable_model" {
  type    = bool
  default = true
}

variable "default_region" {
  type    = string
  default = "us-east-1"
}

variable "log_retention_days" {
  type    = number
  default = 14
}
