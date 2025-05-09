variable "aws_region" {
  description = "AWS region for deploying resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use for authentication"
  type        = string
  default     = "vikram-admin"
}

variable "aws_secret_name" {
  description = "Name of the AWS Secrets Manager secret for API keys"
  type        = string
  default     = "llm-utilities/api-keys"
}

variable "default_llm_provider" {
  description = "Default LLM provider to use"
  type        = string
  default     = "openai"
}

variable "api_stage" {
  description = "API Gateway deployment stage"
  type        = string
  default     = "dev"
}

variable "container_image_uri" {
  description = "URI of the Lambda container image in ECR"
  type        = string
}
