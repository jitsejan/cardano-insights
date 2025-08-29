provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "cardano-insights"
      Service     = "lido-ingestion" 
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}