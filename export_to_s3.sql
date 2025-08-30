-- Export catalyst funding graph data to S3
-- Run with: uv run duckdb catalyst.duckdb -c ".read export_to_s3.sql"

-- Install and load S3 extension
INSTALL httpfs;
LOAD httpfs;

-- Set AWS credentials (configure with your values)
SET s3_region='eu-west-1';
SET s3_access_key_id='YOUR_ACCESS_KEY_ID';
SET s3_secret_access_key='YOUR_SECRET_ACCESS_KEY';

-- Export to S3 as parquet (efficient for analytics)
COPY catalyst_funding_graph 
TO 's3://tech-intelligence-datalake/gold/catalyst_funding_graph/catalyst_funding_graph.parquet';

-- Export to S3 as CSV (for broader compatibility)
COPY catalyst_funding_graph 
TO 's3://tech-intelligence-datalake/gold/catalyst_funding_graph/catalyst_funding_graph.csv';

-- Show export summary
SELECT 
    COUNT(*) as total_records,
    MIN(funding_round) as earliest_fund,
    MAX(funding_round) as latest_fund,
    SUM(amount_ada) as total_ada_funded
FROM catalyst_funding_graph;