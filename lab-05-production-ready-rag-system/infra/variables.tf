variable "project_name" {
  type    = string
  default = "lab-05-production-ready-rag-system"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "authorizer_token" {
  type    = string
  default = "my-secret-token"
}

variable "opensearch_instance_type" {
  type    = string
  default = "t3.small.search"
}

variable "opensearch_domain_name" {
  type    = string
  default = ""
}

variable "opensearch_instance_count" {
  type    = number
  default = 1
}

variable "opensearch_volume_size" {
  type    = number
  default = 10
}

variable "opensearch_index_name" {
  type    = string
  default = "lab05-docs"
}

variable "embedding_model_id" {
  type    = string
  default = "amazon.titan-embed-text-v2:0"
}

variable "embedding_dimension" {
  type    = number
  default = 1024
}

variable "llm_model_id" {
  type    = string
  default = "amazon.nova-pro-v1:0"
}

variable "max_chunks" {
  type    = number
  default = 40
}

variable "documents_bucket_name" {
  type    = string
  default = ""
}

variable "dynamodb_table_name" {
  type    = string
  default = ""
}
