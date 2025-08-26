-- Silver layer: Cleaned and standardized releases  
-- Enriches raw GitHub release data with standardized fields

{{ config(
    materialized='table',
    docs={'node_color': '#C0C0C0'}
) }}

WITH releases_cleaned AS (
    SELECT
        repository_full_name as repository,
        id,
        name as release_name,
        tag_name as tag,
        author.login as release_author,
        published_at,
        created_at,
        updated_at,
        html_url as release_url,
        body,
        draft as is_draft,
        prerelease as is_prerelease,
        fetched_at,
        ROW_NUMBER() OVER (
            PARTITION BY repository_full_name, tag_name 
            ORDER BY published_at DESC
        ) as row_num
    FROM {{ ref('stg_github_releases') }}
    WHERE published_at IS NOT NULL
)

SELECT * FROM releases_cleaned
WHERE row_num = 1