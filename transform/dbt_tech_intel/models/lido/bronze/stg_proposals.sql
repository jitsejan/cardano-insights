{{ config(materialized='table') }}

-- Stage Lido proposals from API
SELECT
    id,
    title,
    fund_id,
    fund_name,
    project_status,
    funding_status,
    amount_requested,
    campaign_name,
    ideascale_link,
    website,
    
    -- Metadata
    ingested_at,
    current_timestamp as dbt_processed_at

FROM {{ source('lido', 'proposals') }}
