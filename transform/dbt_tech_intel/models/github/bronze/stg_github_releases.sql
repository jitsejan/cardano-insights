-- Bronze layer: Raw releases from GitHub API via dlt
-- Raw data with no transformations, direct from dlt pipeline

{{ config(
    materialized='table',
    docs={'node_color': '#8B4513'}
) }}

SELECT 
    *
FROM {{ source('github', 'stg_github_releases') }}