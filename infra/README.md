# Infrastructure - AWS Fargate + S3 + EventBridge + Glue/Athena

Cloud-native infrastructure for Lido Catalyst data ingestion and transformation.

## Architecture

```
EventBridge Schedule → Fargate (Lido dlt) → S3 Bronze → EventBridge Event → Fargate (dbt) → S3 Silver
```

## Components

- **S3**: Data lake storage (bronze/silver/gold)
- **Fargate**: Serverless containers for dlt and dbt
- **EventBridge**: Event-driven orchestration
- **Glue Catalog**: Metadata management for bronze data
- **Athena**: Query engine for dbt transformations
- **ECR**: Container image registry

## Deployment

### Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Terraform state backend** (S3 bucket + DynamoDB table)
3. **VPC and subnets** for Fargate networking
4. **GitHub OIDC** for CI/CD authentication

### Environment Setup

```bash
# Initialize Terraform
cd infra/
terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=cardano-insights/dev/terraform.tfstate" \
  -backend-config="region=us-east-1"

# Plan infrastructure
terraform plan -var-file="env/dev.tfvars"

# Apply infrastructure  
terraform apply -var-file="env/dev.tfvars"
```

### Configuration

Update `env/dev.tfvars` and `env/prod.tfvars` with:
- Your VPC ID and subnet IDs
- Adjust CPU/memory resources
- Set ingestion schedule

## Modules

- `ecr_repo/`: ECR repositories for container images
- `ecs_task/`: Fargate task definitions and roles
- `eventbridge_rule/`: Scheduling and event triggers
- `glue_catalog/`: Data catalog for bronze tables
- `athena_workgroup/`: Query execution environment

## Naming Convention

All resources follow: `${project}-${service}-${environment}`
Example: `cardano-insights-lido-ingestion-prod`