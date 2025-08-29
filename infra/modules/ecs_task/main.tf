resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-${var.service_name}"
  tags = var.tags

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# IAM role for task execution
resource "aws_iam_role" "execution" {
  name = "${var.name_prefix}-${var.service_name}-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM role for task (application permissions)
resource "aws_iam_role" "task" {
  name = "${var.name_prefix}-${var.service_name}-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# S3 permissions for the task
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.name_prefix}-${var.service_name}-s3"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket}",
          "arn:aws:s3:::${var.s3_bucket}/*"
        ]
      }
    ]
  })
}

# DynamoDB permissions for GitHub pipeline state tracking
resource "aws_iam_role_policy" "dynamodb_access" {
  count = var.dynamodb_table != null ? 1 : 0
  name  = "${var.name_prefix}-${var.service_name}-dynamodb"
  role  = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = "arn:aws:dynamodb:*:*:table/${var.dynamodb_table}"
      }
    ]
  })
}

# EventBridge permissions
resource "aws_iam_role_policy" "eventbridge_access" {
  name = "${var.name_prefix}-${var.service_name}-eventbridge"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Security group for ECS tasks
resource "aws_security_group" "task" {
  name        = "${var.name_prefix}-${var.service_name}-task"
  description = "Security group for ${var.service_name} ECS task"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-${var.service_name}-task"
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = "${var.name_prefix}-${var.service_name}"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = var.cpu
  memory                  = var.memory
  execution_role_arn      = aws_iam_role.execution.arn
  task_role_arn           = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name  = var.service_name
      image = var.image_uri
      
      environment = concat([
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "S3_BUCKET"
          value = var.s3_bucket
        },
        {
          name  = "S3_PREFIX"
          value = var.s3_prefix
        },
        {
          name  = "EVENTBRIDGE_BUS_NAME"
          value = var.eventbridge_bus
        }
      ], var.dynamodb_table != null ? [{
        name  = "DYNAMODB_STATE_TABLE"
        value = var.dynamodb_table
      }] : [])

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.name_prefix}-${var.service_name}"
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = var.tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${var.name_prefix}-${var.service_name}"
  retention_in_days = 7
  tags              = var.tags
}

data "aws_region" "current" {}