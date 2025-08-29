# Cloud-Native Architecture Migration

## Overview

Migration from local DuckDB to AWS cloud-native data platform:

```
Lido API → Fargate (dlt) → S3 Bronze → EventBridge → Fargate (dbt+Athena) → S3 Silver
```

## Repository Structure

```
.
├── load/                          # dlt pipelines (Fargate containers)
│   ├── lido/
│   │   ├── pipeline.py            # dlt → S3 Parquet bronze
│   │   ├── settings.py            # environment configuration
│   │   ├── requirements.txt       # container dependencies
│   │   └── Dockerfile             # Fargate image
│   └── common/                    # shared utilities
│       └── utils.py               # logging, events, AWS helpers
│
├── transform/                     # dbt (Athena) transformations
│   ├── dbt_catalyst/              # Catalyst-specific models
│   ├── dbt_github/                # GitHub models (future)
│   ├── dbt_shared/                # shared macros/seeds
│   ├── profiles/                  # runtime profiles
│   │   └── profiles.yml.j2        # Athena configuration template
│   └── Dockerfile                 # dbt-athena container
│
├── infra/                         # Terraform infrastructure
│   ├── modules/                   # reusable Terraform modules
│   ├── env/                       # environment-specific configs
│   └── main.tf                    # primary infrastructure
│
├── .github/workflows/             # CI/CD automation  
│   ├── docker-build.yml           # ECR image builds
│   ├── terraform-apply.yml        # infrastructure deployment
│   └── dbt-dev.yml                # dbt validation
│
└── scripts/                       # local development utilities
    └── run_local_lido.py          # local pipeline testing
```

## Runtime Flow

1. **EventBridge Schedule** → Triggers Lido ingestion (Fargate)
2. **Lido Container** (dlt) → Writes Parquet to `s3://.../bronze/lido/`
3. **Success Event** → EventBridge emits `techint.lido/ingestion.complete`
4. **dbt Container** (Fargate) → Triggered by event, runs Athena transformations
5. **Silver Output** → dbt writes results to `s3://.../silver/catalyst/`

## Key Benefits

- ✅ **Serverless**: Fargate scales automatically, no server management
- ✅ **Event-driven**: EventBridge eliminates complex orchestration  
- ✅ **Standard tooling**: dlt + dbt + Athena industry practices
- ✅ **Cost-effective**: Pay per execution, no idle resources
- ✅ **Scalable**: S3 + Athena handle petabyte-scale data
- ✅ **Environment isolation**: Clean dev/prod separation

## Migration Path

1. **Phase 1**: Create cloud infrastructure (current)
2. **Phase 2**: Migrate existing dbt models to Athena
3. **Phase 3**: Deploy containers and test end-to-end
4. **Phase 4**: Add GitHub ingestion to cloud architecture
5. **Phase 5**: Sunset local DuckDB setup

## Development Workflow

```bash
# Local development
make run-local-lido          # Test pipeline locally
make dbt-dev-athena          # Test dbt against dev Athena

# Cloud deployment
git push origin feature-branch  # Triggers CI/CD
# → Builds containers → Deploys to dev → Runs validation

# Production deployment  
gh workflow run terraform-apply.yml -f environment=prod -f action=apply
```