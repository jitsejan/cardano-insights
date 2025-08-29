# Glue Catalog module for bronze data discovery

resource "aws_glue_catalog_database" "bronze" {
  name         = "${var.name_prefix}-bronze"
  description  = "Bronze layer data catalog for ${var.name_prefix}"
  
  tags = var.tags
}

resource "aws_glue_crawler" "bronze_lido" {
  database_name = aws_glue_catalog_database.bronze.name
  name          = "${var.name_prefix}-bronze-lido"
  role          = aws_iam_role.crawler.arn
  description   = "Crawler for Lido bronze data in S3"

  s3_target {
    path = "s3://${var.s3_bucket}/${var.s3_prefix}/"
  }

  # Run crawler after new data arrives
  schedule = "cron(0 */6 * * ? *)"  # Every 6 hours

  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  tags = var.tags
}

# IAM role for Glue Crawler
resource "aws_iam_role" "crawler" {
  name = "${var.name_prefix}-glue-crawler"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "crawler_service" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
  role       = aws_iam_role.crawler.name
}

resource "aws_iam_role_policy" "crawler_s3" {
  name = "${var.name_prefix}-crawler-s3"
  role = aws_iam_role.crawler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket}",
          "arn:aws:s3:::${var.s3_bucket}/${var.s3_prefix}/*"
        ]
      }
    ]
  })
}