variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be staging or production."
  }

}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "api_image" {
  type    = string
  default = "public.ecr.aws/docker/library/python:3.12-slim"
}

variable "worker_image" {
  type    = string
  default = "public.ecr.aws/docker/library/python:3.12-slim"
}

variable "oidc_issuer" {
  type      = string
  sensitive = true
}

variable "oidc_jwks_url" {
  type      = string
  sensitive = true
}

variable "oidc_audience" {
  type    = string
  default = "creditflow-api"
}

variable "certificate_arn" {
  type        = string
  description = "Validated ACM certificate for the public API hostname"
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "database_instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}

