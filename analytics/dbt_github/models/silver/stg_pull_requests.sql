-- Silver layer: Cleaned and standardized pull requests
-- Enriches raw GitHub PR data with standardized fields and classifications

{{ config(
    materialized='table',
    docs={'node_color': '#C0C0C0'}
) }}

WITH pull_requests_cleaned AS (
    SELECT
        repository_full_name as repository,
        id,
        number,
        title,
        body as description,
        state,
        -- These fields may not be available in the GitHub API response
        -- additions,
        -- deletions, 
        -- changed_files,
        -- commits,
        user__login as author,
        base__ref as base_branch,
        head__ref as head_branch,
        -- Labels are structured differently in our data
        -- labels_json,
        -- labels_list,
        html_url as url,
        created_at,
        closed_at,
        merged_at,
        fetched_at,
        -- Add feature classification logic here
        CASE 
            WHEN lower(title) LIKE '%fix%' OR lower(title) LIKE '%bug%' THEN 'bug fix'
            WHEN lower(title) LIKE '%feat%' OR lower(title) LIKE '%add%' OR lower(title) LIKE '%implement%' THEN 'feature'
            WHEN lower(title) LIKE '%refactor%' OR lower(title) LIKE '%clean%' THEN 'refactor'
            WHEN lower(title) LIKE '%test%' THEN 'test'
            WHEN lower(title) LIKE '%doc%' THEN 'documentation'
            ELSE 'not clear'
        END as feat_classifier
    FROM {{ ref('stg_github_pull_requests') }}
)

SELECT * FROM pull_requests_cleaned