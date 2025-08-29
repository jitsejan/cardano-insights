variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "service_name" {
  description = "Name of the service (lido, github, dbt)"
  type        = string
}

variable "image_uri" {
  description = "URI of the container image"
  type        = string
}

variable "cpu" {
  description = "CPU units for the task"
  type        = number
}

variable "memory" {
  description = "Memory (MiB) for the task"
  type        = number
}

variable "s3_bucket" {
  description = "S3 bucket for data storage"
  type        = string
}

variable "s3_prefix" {
  description = "S3 prefix for this service"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "eventbridge_bus" {
  description = "EventBridge bus name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for security group"
  type        = string
  default     = null
}

variable "dynamodb_table" {
  description = "DynamoDB table name for state tracking (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}