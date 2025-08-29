output "database_name" {
  description = "Name of the Glue Catalog database"
  value       = aws_glue_catalog_database.bronze.name
}

output "database_arn" {
  description = "ARN of the Glue Catalog database"
  value       = aws_glue_catalog_database.bronze.arn
}

output "crawler_name" {
  description = "Name of the Glue Crawler"
  value       = aws_glue_crawler.bronze_lido.name
}

output "crawler_arn" {
  description = "ARN of the Glue Crawler"
  value       = aws_glue_crawler.bronze_lido.arn
}