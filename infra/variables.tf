variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID for Fargate tasks"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Fargate tasks"
  type        = list(string)
}

variable "ingestion_schedule" {
  description = "EventBridge schedule expression for Lido ingestion"
  type        = string
  default     = "rate(6 hours)"  # Run every 6 hours
}

variable "eventbridge_bus_name" {
  description = "EventBridge custom bus name (default for default bus)"
  type        = string
  default     = "default"
}

# Lido task configuration
variable "lido_cpu" {
  description = "CPU units for Lido ingestion task"
  type        = number
  default     = 512  # 0.5 vCPU
}

variable "lido_memory" {
  description = "Memory (MiB) for Lido ingestion task"
  type        = number
  default     = 1024  # 1 GB
}

# GitHub task configuration
variable "github_cpu" {
  description = "CPU units for GitHub ingestion task"
  type        = number
  default     = 512  # 0.5 vCPU
}

variable "github_memory" {
  description = "Memory (MiB) for GitHub ingestion task"
  type        = number
  default     = 1024  # 1 GB
}

# dbt task configuration
variable "dbt_cpu" {
  description = "CPU units for dbt transformation task"
  type        = number
  default     = 1024  # 1 vCPU
}

variable "dbt_memory" {
  description = "Memory (MiB) for dbt transformation task"
  type        = number
  default     = 2048  # 2 GB
}

# Optional: KMS key for encryption
variable "kms_key_id" {
  description = "KMS key ID for S3 encryption (optional)"
  type        = string
  default     = null
}