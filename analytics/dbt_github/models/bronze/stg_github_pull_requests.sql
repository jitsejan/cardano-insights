-- Bronze layer: Raw pull requests from GitHub API via dlt
-- Raw data with no transformations, direct from dlt pipeline

{{ config(
    materialized='table',
    docs={'node_color': '#8B4513'}
) }}

SELECT 
    *
FROM {{ source('bronze', 'github_prs') }}