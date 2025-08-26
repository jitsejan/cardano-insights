-- Create or open unified DB
.open tech_intel.duckdb;

-- Standard schemas
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS map;
CREATE SCHEMA IF NOT EXISTS gold;

-- Attach sources (read-only)
-- Note: For now, GitHub database is empty - we'll create placeholder structure
-- ATTACH '../github-trend-insights/github_insights.duckdb' AS gh (READ_ONLY);
ATTACH 'cardano_data.duckdb' AS cdo (READ_ONLY);

-- ======= CONFIG: choose linking strategy =======
-- Set this flag manually before running:
-- 0 = create VIEWS (zero-copy, default)
-- 1 = create TABLES (materialize/copy)
-- DuckDB CLI can't use variables; pick ONE block below.

-- ======= OPTION A: ZERO-COPY VIEWS (default) =======
-- GitHub bronze views - create empty placeholder tables for now
CREATE OR REPLACE TABLE bronze.github_repos AS 
SELECT * FROM (VALUES 
    (1, 'placeholder-owner/placeholder-repo', 'Placeholder Repository', 'A placeholder repository', 
     '2025-01-01T00:00:00Z'::TIMESTAMP, '2025-01-01T00:00:00Z'::TIMESTAMP, 
     FALSE, FALSE, 0, 0, 0, 'main', 'MIT')
) AS t(id, full_name, name, description, created_at, updated_at, private, fork, stargazers_count, forks_count, open_issues_count, default_branch, license);

CREATE OR REPLACE TABLE bronze.github_prs AS 
SELECT * FROM (VALUES 
    (1, 1, 'Sample PR', 'A sample pull request', 'closed', 
     '2025-01-01T00:00:00Z'::TIMESTAMP, '2025-01-01T00:00:00Z'::TIMESTAMP,
     'placeholder-owner/placeholder-repo', TRUE)
) AS t(id, number, title, body, state, created_at, merged_at, repository_full_name, merged);

CREATE OR REPLACE TABLE bronze.github_releases AS 
SELECT * FROM (VALUES 
    (1, 'v1.0.0', 'Release 1.0.0', 'Initial release', 
     '2025-01-01T00:00:00Z'::TIMESTAMP, FALSE, FALSE,
     'placeholder-owner/placeholder-repo')
) AS t(id, tag_name, name, body, published_at, draft, prerelease, repository_full_name);

-- Catalyst (Cardano insights) bronze views
CREATE OR REPLACE VIEW bronze.catalyst_proposals AS SELECT * FROM cdo.lido_raw.proposals;
CREATE OR REPLACE VIEW bronze.catalyst_funds AS SELECT * FROM cdo.lido_raw.funds;

-- ======= OPTION B: PHYSICAL COPY (COMMENT OUT VIEWS ABOVE, UNCOMMENT BELOW) =======
-- CREATE TABLE bronze.github_repos       AS SELECT * FROM gh.main.github_repositories;
-- CREATE TABLE bronze.github_prs         AS SELECT * FROM gh.main.github_pull_requests;
-- CREATE TABLE bronze.github_releases    AS SELECT * FROM gh.main.github_releases;
-- CREATE TABLE bronze.catalyst_proposals AS SELECT * FROM cdo.lido_raw.proposals;
-- CREATE TABLE bronze.catalyst_funds     AS SELECT * FROM cdo.lido_raw.funds;

-- Sanity checks
SELECT 'github_repos' AS table, COUNT(*) AS n FROM bronze.github_repos;
SELECT 'github_prs' AS table, COUNT(*) AS n FROM bronze.github_prs;
SELECT 'github_releases' AS table, COUNT(*) AS n FROM bronze.github_releases;
SELECT 'catalyst_proposals' AS table, COUNT(*) AS n FROM bronze.catalyst_proposals;
SELECT 'catalyst_funds' AS table, COUNT(*) AS n FROM bronze.catalyst_funds;