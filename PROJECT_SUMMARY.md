# Cardano Insights - Project Summary

## Overview

**Cardano Insights** is a modern data analytics platform for the Cardano ecosystem, specifically focused on Catalyst funding data and wallet ecosystem intelligence. The project follows modern data engineering patterns with a clear separation between raw data ingestion (dlt) and analytics transformation (dbt).

## Architecture

### Data Stack
- **Ingestion**: dlt (data load tool) for raw API extraction
- **Transformation**: dbt for analytics and enrichment
- **Database**: DuckDB for local analytics
- **Testing**: pytest with comprehensive parametrized testing

### Layer Architecture
```
Bronze Layer (Raw Staging)
├── stg_funds.sql - Catalyst funding rounds
└── stg_proposals.sql - Raw proposal data

Silver Layer (Enrichment)
└── proposals_enriched.sql - Wallet detection, funding analysis, GitHub parsing

Gold Layer (Analytics Marts)
├── funded_projects_summary.sql - Funding analytics by fund
├── wallet_ecosystem_analysis.sql - Wallet project analysis
└── lace_competitive_landscape.sql - Strategic competitive intelligence
```

## Key Features

### 1. **Catalyst Funding Analytics**
- Complete funding data from Lido Nation Catalyst Explorer API
- 12+ Catalyst funds (F1-F13+) with 10,000+ proposals
- Funding success rates, approval metrics, GitHub adoption tracking

### 2. **Wallet Ecosystem Intelligence**
- **Wallet Detection**: Automatically identifies wallet-related projects
- **Competition Analysis**: Categorizes Lace competitors by threat level
- **Strategic Scoring**: Prioritizes projects for competitive monitoring

#### Competition Categories:
- `direct_competitor` - Browser/web wallets (direct Lace competition)
- `existing_competitor` - Established wallets (Yoroi, Eternl, Nami, Flint)
- `indirect_competitor` - Mobile/desktop wallets  
- `ecosystem_enabler` - Wallet infrastructure & tooling

### 3. **Analytics & Reporting**
- Funding trends across Catalyst rounds
- Success pattern analysis (funding vs GitHub activity)
- Competitive landscape monitoring
- Ecosystem health metrics

## Project Structure

```
cardano-insights/
├── src/cardano_insights/connectors/
│   └── lido.py                    # Simplified raw data connector
├── models/                        # dbt analytics models
│   ├── bronze/                    # Raw staging
│   ├── silver/                    # Enrichment layer  
│   └── gold/                      # Analytics marts
├── tests/                         # Comprehensive pytest suite
├── dbt_project.yml               # dbt configuration
├── profiles.yml                  # Database configuration
├── Makefile                      # Development commands
└── pyproject.toml               # Dependencies & configuration
```

## Development Workflow

### Data Pipeline Commands
```bash
# Data Extraction
make extract-lido        # Sample extraction (2 pages)
make extract-lido-full   # Full extraction (~10k proposals)

# Analytics Pipeline  
make dbt-run            # Run dbt models (bronze → silver → gold)
make analytics-full     # Full pipeline: extract + transform

# Documentation
make dbt-docs           # Generate and serve dbt documentation
```

### Testing Commands
```bash
make test               # Fast unit tests (~0.29s)
make test-integration   # API integration tests
make test-all           # All tests including slow ones
```

## Key Analytics Tables

### 1. `funded_projects_summary`
- Funding metrics by Catalyst fund
- GitHub adoption rates
- Wallet ecosystem project counts
- Success rate analysis

### 2. `wallet_ecosystem_analysis`  
- Detailed wallet project breakdown
- Competition level classification
- Funding success by wallet type
- GitHub repository tracking

### 3. `lace_competitive_landscape`
- Strategic competitive analysis for Lace wallet
- Priority scoring for monitoring
- Funding success rates by competition level
- Top funded competitor examples

## Technical Highlights

### 1. **Modern Data Engineering Patterns**
- Clean separation: dlt (ingestion) + dbt (transformation)
- Bronze/Silver/Gold medallion architecture
- Comprehensive testing with pytest parametrization
- Professional development workflow with Makefile

### 2. **Simplified Connector Architecture**
```python
# Clean, focused connector
@dlt.resource(name="funds", primary_key="id")
def funds() -> Iterator[Dict[str, Any]]:
    """Raw Catalyst funds data"""

@dlt.resource(name="proposals", primary_key="id") 
def proposals(fund_id: Optional[int] = None, max_pages: Optional[int] = None):
    """Raw proposal data - enrichment handled by dbt"""
```

### 3. **Advanced Analytics SQL**
- Wallet ecosystem detection via pattern matching
- Competition level classification
- Strategic priority scoring algorithms
- Cross-fund trend analysis

## Business Value

### Strategic Intelligence for Lace Wallet
- **Competitive Monitoring**: Identify and track Lace competitors
- **Ecosystem Health**: Monitor wallet innovation trends
- **Investment Tracking**: See which wallet projects get funded
- **Success Patterns**: Understand what makes wallet projects successful

### Ecosystem Analytics
- **Funding Trends**: Track Catalyst ecosystem growth
- **Success Metrics**: Correlation between funding and development activity
- **Innovation Tracking**: Emerging technologies and approaches

## Future Roadmap

### Phase 1: Unification (Next)
- Merge with `github-trend-insights` project
- Create unified data platform with shared bronze/silver/gold layers
- Cross-platform analysis (Catalyst funding → GitHub development activity)

### Phase 2: Enhancement
- Real-time GitHub activity tracking for funded projects
- Development velocity vs funding correlation analysis
- Automated competitive intelligence alerts

### Phase 3: Intelligence Platform
- Predictive analytics for project success
- Ecosystem health scoring
- Strategic decision support dashboards

## Technical Decisions & Rationale

### 1. **Why dbt over Python for Analytics?**
- **SQL-first approach**: More accessible to business analysts
- **Documentation**: Auto-generated docs for all models
- **Testing**: Built-in data quality testing
- **Lineage**: Automatic data lineage tracking
- **Collaboration**: Easy to review and modify analytics logic

### 2. **Why DuckDB over PostgreSQL?**
- **Local development**: No database setup required
- **Performance**: Excellent analytical performance
- **Portability**: Database file can be easily shared
- **Analytics focus**: Optimized for OLAP workloads

### 3. **Why Simplified Connector Architecture?**
- **Separation of concerns**: dlt for ingestion, dbt for logic
- **Maintainability**: Easier to debug and modify
- **Scalability**: Can easily add new connectors (GitHub, etc.)
- **Testing**: Unit tests for ingestion, dbt tests for analytics

## Getting Started

### Prerequisites
- Python 3.11+
- uv package manager

### Quick Start
```bash
# Install dependencies
make install

# Extract sample data
make extract-lido

# Run analytics pipeline
make dbt-run

# View results in DuckDB
# Tables: stg_funds, stg_proposals, proposals_enriched, 
#         funded_projects_summary, wallet_ecosystem_analysis,
#         lace_competitive_landscape
```

## Testing Strategy

### Multi-Layer Testing
- **Unit Tests**: Fast connector function testing (15 tests, ~0.29s)
- **Integration Tests**: API connectivity and data structure validation  
- **Parametrized Testing**: Comprehensive scenario coverage
- **Data Quality Tests**: dbt built-in testing for analytics

### Test Organization
```
tests/
├── connectors/test_lido.py     # Connector testing
├── test_basic.py               # Infrastructure testing
└── conftest.py                 # Shared fixtures
```

## Development Status

### Completed ✅
- Modern dbt architecture implementation
- Comprehensive wallet ecosystem analytics
- Strategic competitive intelligence for Lace
- Clean connector architecture
- Professional testing suite
- Development workflow automation

### In Progress 🚧
- PR #3 ready for review: "Add dbt architecture with wallet ecosystem analytics"

### Planned 📋
- Merge with github-trend-insights for unified platform
- Cross-platform analytics (funding → development activity)
- Real-time competitive intelligence

---

## Contact & Collaboration

This project serves as a foundation for strategic decision-making in the Cardano wallet ecosystem and demonstrates modern data engineering practices for cryptocurrency analytics.

**Key Differentiators:**
- Strategic business focus (not just data for data's sake)
- Modern data stack (dlt + dbt)
- Competitive intelligence capabilities
- Clean, maintainable architecture
- Comprehensive testing and documentation