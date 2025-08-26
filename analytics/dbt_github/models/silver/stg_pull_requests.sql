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
        additions,
        deletions,
        changed_files,
        commits,
        user.login as author,
        base.ref as base_branch,
        head.ref as head_branch,
        -- Convert labels array to JSON string for compatibility
        CASE 
            WHEN labels IS NOT NULL 
            THEN array_to_json(labels)
            ELSE '[]'::json
        END as labels_json,
        -- Extract label names as array
        CASE 
            WHEN labels IS NOT NULL 
            THEN array_transform(labels, x -> x.name)
            ELSE []
        END as labels_list,
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