variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Name prefix for resources"
  default     = "secure-bedrock-gateway"
}

variable "owner" {
  type        = string
  description = "Owner of the resources"
  default     = "platform-team"
}

variable "billing" {
  type        = string
  description = "Billing identifier"
  default     = "shared"
}

variable "creation_date" {
  type        = string
  description = "Date resources were created (YYYY-MM-DD)"
  default     = "2026-03-09"
}

variable "lambda_timeout" {
  type        = number
  description = "Lambda timeout in seconds"
  default     = 30
}

variable "lambda_memory" {
  type        = number
  description = "Lambda memory size in MB"
  default     = 512
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention in days"
  default     = 14
}

variable "default_model_id" {
  type        = string
  description = "Default Bedrock model ID"
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}

variable "max_prompt_length" {
  type        = number
  description = "Maximum prompt length"
  default     = 4000
}

variable "log_level" {
  type        = string
  description = "Application log level"
  default     = "INFO"
}
