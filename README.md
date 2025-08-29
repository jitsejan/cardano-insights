# Cardano Insights Platform

Cloud-native data platform for analyzing Cardano ecosystem activity through Catalyst governance data and GitHub development metrics.

## Architecture

**Data Flow:** `Ingestion (Fargate) → S3 Data Lake → Transformation (dbt + Athena)`

### Core Components

- **Ingestion Pipelines** (`load/`): dlt-based containers running on AWS Fargate
  - `load/lido/`: Catalyst governance data from Lido Nation API
  - `load/github/`: Development activity from GitHub API
- **Transformations** (`transform/`): dbt models on AWS Athena
- **Infrastructure** (`infra/`): Terraform modules for AWS resources
- **CI/CD** (`ci/`): GitHub Actions for container builds and deployments

### Environment Strategy

#### Development
- **State Tracking**: DuckDB (local analysis)
- **Data Storage**: Dual-write to DuckDB + S3 dev bucket
- **Purpose**: Local development with cloud pipeline testing

#### Production  
- **State Tracking**: DynamoDB (persistent, distributed)
- **Data Storage**: S3 data lake only
- **Orchestration**: EventBridge + Fargate tasks

## Data Sources

### Lido Nation (Catalyst)
- **Strategy**: Full dump (no incremental)
- **Data**: Funds, proposals, voting results
- **API**: `https://www.lidonation.com/api/catalyst-explorer/`

### GitHub
- **Strategy**: Incremental loading with state tracking
- **Data**: Repository metadata, pull requests, releases, issues
- **Repositories**: Cardano Foundation, IOG, Emurgo projects
- **Rate Limiting**: Respects GitHub API limits with authentication

## Infrastructure

### AWS Resources
- **S3**: Bronze/silver/gold data lake structure
- **Fargate**: Containerized ingestion tasks
- **EventBridge**: Event-driven orchestration
- **Glue Catalog**: Schema registry and metadata
- **Athena**: SQL transformation engine
- **DynamoDB**: Production state tracking

### Container Strategy
- One Dockerfile per ingestion source (`lido`, `github`)  
- Single dbt container for all transformations
- ECR repositories for image storage

## Development

### Setup
```bash
uv sync
cp .env.example .env  # Configure API keys
```

### Testing
```bash
# Fast unit tests
uv run pytest -m "not integration and not slow"

# Integration tests (requires API keys)  
uv run pytest -m "integration"

# All tests including slow ones
uv run pytest
```

### Running Pipelines

#### Local Development
```bash
# Lido pipeline (dev mode - dual write)
ENVIRONMENT=dev uv run python -m load.lido.pipeline

# GitHub pipeline (dev mode - dual write)
ENVIRONMENT=dev GITHUB_TOKEN=<token> uv run python -m load.github.pipeline
```

#### Production Simulation
```bash
# Requires AWS credentials and S3 bucket
ENVIRONMENT=prod S3_BUCKET=<bucket> uv run python -m load.lido.pipeline
```

## Data Model

### Bronze Layer (Raw)
- Direct API responses with minimal transformation
- Timestamped for lineage tracking
- Stored as Parquet in S3

### Silver Layer (Cleaned)
- Standardized schemas via dbt
- Data quality checks and deduplication
- GitHub repository enrichment

### Gold Layer (Analytics-Ready)
- Business metrics and KPIs  
- Aggregated views for dashboards
- Cross-source data relationships

## Status

 **Infrastructure**: Terraform modules for complete AWS deployment  
 **Ingestion**: Both Lido and GitHub pipelines operational  
 **State Management**: Environment-aware tracking (DuckDB dev, DynamoDB prod)  
 **Testing**: Comprehensive test coverage (56 tests passing)  
 **CI/CD**: GitHub Actions for automated builds  
=� **Transformations**: dbt models (scaffold ready)  
=� **Deployment**: Cloud deployment pending infrastructure provisioning