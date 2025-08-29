variable "name_prefix" {
  description = "Prefix for naming Glue resources"
  type        = string
}

variable "s3_bucket" {
  description = "S3 bucket name for bronze data"
  type        = string
}

variable "s3_prefix" {
  description = "S3 prefix for bronze data"
  type        = string
}

variable "tags" {
  description = "Tags to apply to Glue resources"
  type        = map(string)
  default     = {}
}