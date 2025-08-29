terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Configure backend for state management
  backend "s3" {
    # Backend configuration will be provided via -backend-config during init
    # bucket         = "your-terraform-state-bucket"
    # key            = "cardano-insights/terraform.tfstate"  
    # region         = "us-east-1"
    # encrypt        = true
    # dynamodb_table = "terraform-lock-table"
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values
locals {
  project_name = "cardano-insights"
  service_name = "lido-ingestion"
  environment  = var.environment
  
  # Naming convention: ${project}-${service}-${environment}
  name_prefix = "${local.project_name}-${local.service_name}-${local.environment}"
  
  # Common tags
  common_tags = {
    Project     = local.project_name
    Service     = local.service_name
    Environment = local.environment
    ManagedBy   = "terraform"
  }
  
  # S3 configuration
  s3_bucket = "${local.name_prefix}-data"
  s3_prefixes = {
    bronze = "bronze/lido"
    silver = "silver/catalyst"
    gold   = "gold/catalyst"
    athena = "athena-results"
  }
}

# DynamoDB table for GitHub pipeline state tracking
resource "aws_dynamodb_table" "github_state" {
  name           = "${local.name_prefix}-github-state"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "pipeline_state_id"

  attribute {
    name = "pipeline_state_id"
    type = "S"
  }

  tags = merge(local.common_tags, {
    Name        = "${local.name_prefix}-github-state"
    Description = "State tracking for GitHub data pipeline"
  })
}

# S3 Bucket for data storage
resource "aws_s3_bucket" "data" {
  bucket = local.s3_bucket
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ECR repositories for container images
module "ecr_lido" {
  source = "./modules/ecr_repo"
  
  name = "${local.name_prefix}-lido"
  tags = local.common_tags
}

module "ecr_github" {
  source = "./modules/ecr_repo"
  
  name = "${local.name_prefix}-github"
  tags = local.common_tags
}

module "ecr_dbt" {
  source = "./modules/ecr_repo"
  
  name = "${local.name_prefix}-dbt"
  tags = local.common_tags
}

# Glue Catalog for bronze data
module "glue_catalog" {
  source = "./modules/glue_catalog"
  
  name_prefix = local.name_prefix
  s3_bucket   = aws_s3_bucket.data.bucket
  s3_prefix   = local.s3_prefixes.bronze
  tags        = local.common_tags
}

# Athena Workgroup
module "athena_workgroup" {
  source = "./modules/athena_workgroup"
  
  name                = "${local.name_prefix}-workgroup"
  results_bucket      = aws_s3_bucket.data.bucket
  results_prefix      = local.s3_prefixes.athena
  glue_database_name  = module.glue_catalog.database_name
  tags                = local.common_tags
}

# ECS Task for Lido ingestion
module "ecs_task_lido" {
  source = "./modules/ecs_task"
  
  name_prefix       = local.name_prefix
  service_name      = "lido"
  image_uri         = "${module.ecr_lido.repository_url}:latest"
  cpu               = var.lido_cpu
  memory            = var.lido_memory
  s3_bucket         = aws_s3_bucket.data.bucket
  s3_prefix         = local.s3_prefixes.bronze
  environment       = local.environment
  eventbridge_bus   = var.eventbridge_bus_name
  vpc_id            = var.vpc_id
  tags              = local.common_tags
}

# ECS Task for GitHub ingestion
module "ecs_task_github" {
  source = "./modules/ecs_task"
  
  name_prefix       = local.name_prefix
  service_name      = "github"
  image_uri         = "${module.ecr_github.repository_url}:latest"
  cpu               = var.github_cpu
  memory            = var.github_memory
  s3_bucket         = aws_s3_bucket.data.bucket
  s3_prefix         = "bronze/github"
  environment       = local.environment
  eventbridge_bus   = var.eventbridge_bus_name
  dynamodb_table    = aws_dynamodb_table.github_state.name
  vpc_id            = var.vpc_id
  tags              = local.common_tags
}

# ECS Task for dbt transformation
module "ecs_task_dbt" {
  source = "./modules/ecs_task"
  
  name_prefix       = local.name_prefix
  service_name      = "dbt"
  image_uri         = "${module.ecr_dbt.repository_url}:latest"
  cpu               = var.dbt_cpu
  memory            = var.dbt_memory
  s3_bucket         = aws_s3_bucket.data.bucket
  s3_prefix         = local.s3_prefixes.silver
  environment       = local.environment
  glue_database     = module.glue_catalog.database_name
  athena_workgroup  = module.athena_workgroup.workgroup_name
  vpc_id            = var.vpc_id
  tags              = local.common_tags
}

# EventBridge rules for orchestration
module "eventbridge_schedule" {
  source = "./modules/eventbridge_rule"
  
  name_prefix     = local.name_prefix
  rule_type       = "schedule"
  schedule_expression = var.ingestion_schedule
  target_task_arn = module.ecs_task_lido.task_definition_arn
  cluster_arn     = module.ecs_task_lido.cluster_arn
  subnet_ids      = var.private_subnet_ids
  security_group_ids = [module.ecs_task_lido.security_group_id]
  tags            = local.common_tags
}

module "eventbridge_trigger" {
  source = "./modules/eventbridge_rule"
  
  name_prefix     = local.name_prefix
  rule_type       = "event"
  event_pattern = {
    source       = ["techint.lido"]
    detail-type  = ["ingestion.complete"]
    detail = {
      env = [local.environment]
    }
  }
  target_task_arn = module.ecs_task_dbt.task_definition_arn
  cluster_arn     = module.ecs_task_dbt.cluster_arn
  subnet_ids      = var.private_subnet_ids
  security_group_ids = [module.ecs_task_dbt.security_group_id]
  tags            = local.common_tags
}