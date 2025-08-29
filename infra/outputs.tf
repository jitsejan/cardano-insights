output "s3_bucket_name" {
  description = "Name of the S3 bucket for data storage"
  value       = aws_s3_bucket.data.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for data storage"
  value       = aws_s3_bucket.data.arn
}

output "glue_database_name" {
  description = "Name of the Glue Catalog database"
  value       = module.glue_catalog.database_name
}

output "glue_crawler_name" {
  description = "Name of the Glue Crawler for bronze data"
  value       = module.glue_catalog.crawler_name
}

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = module.athena_workgroup.workgroup_name
}

output "ecr_lido_repository_url" {
  description = "ECR repository URL for Lido container"
  value       = module.ecr_lido.repository_url
}

output "ecr_dbt_repository_url" {
  description = "ECR repository URL for dbt container"
  value       = module.ecr_dbt.repository_url
}

output "lido_task_definition_arn" {
  description = "ARN of the Lido ECS task definition"
  value       = module.ecs_task_lido.task_definition_arn
}

output "dbt_task_definition_arn" {
  description = "ARN of the dbt ECS task definition"
  value       = module.ecs_task_dbt.task_definition_arn
}

output "lido_schedule_rule_name" {
  description = "Name of the EventBridge schedule rule for Lido"
  value       = module.eventbridge_schedule.rule_name
}

output "dbt_trigger_rule_name" {
  description = "Name of the EventBridge trigger rule for dbt"
  value       = module.eventbridge_trigger.rule_name
}