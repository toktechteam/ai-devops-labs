variable "project_name" {
  type    = string
  default = "lab-08-ai-security-guardrails"
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

variable "max_prompt_chars" {
  type    = number
  default = 2000
}

variable "policy_mode" {
  type    = string
  default = "strict"
}

variable "log_retention_days" {
  type    = number
  default = 14
}
