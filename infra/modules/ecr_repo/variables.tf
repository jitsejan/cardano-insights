variable "name" {
  description = "Name of the ECR repository"
  type        = string
}

variable "tags" {
  description = "Tags to apply to ECR repository"
  type        = map(string)
  default     = {}
}