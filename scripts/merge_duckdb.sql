-- Create or open unified DB
.open tech_intel.duckdb;

-- Standard schemas
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS map;
CREATE SCHEMA IF NOT EXISTS gold;

-- Attach sources (read-only)
ATTACH 'github_data.duckdb' AS gh (READ_ONLY);
ATTACH 'cardano_data.duckdb' AS cdo (READ_ONLY);

-- ======= CONFIG: choose linking strategy =======
-- Set this flag manually before running:
-- 0 = create VIEWS (zero-copy, default)
-- 1 = create TABLES (materialize/copy)
-- DuckDB CLI can't use variables; pick ONE block below.

-- ======= OPTION A: ZERO-COPY VIEWS (default) =======
-- GitHub bronze views - real data from GitHub API
CREATE OR REPLACE VIEW bronze.github_repos AS SELECT * FROM gh.github_raw.repositories;
CREATE OR REPLACE VIEW bronze.github_prs AS SELECT * FROM gh.github_raw.pull_requests;
CREATE OR REPLACE VIEW bronze.github_releases AS SELECT * FROM gh.github_raw.releases;

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