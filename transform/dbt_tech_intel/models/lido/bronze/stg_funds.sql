{{ config(materialized='table') }}

-- Stage Lido funds from API
SELECT
    id,
    title,
    id as fund_number,
    proposals_count,
    amount as funding_available,
    currency,
    launch_date,
    currency_symbol,
    link as fund_link,
    thumbnail_url,
    slug,
    content as description,
    content as excerpt,
    label,
    funded_proposals,
    
    -- Metadata
    ingested_at,
    current_timestamp as dbt_processed_at

FROM {{ source('lido', 'funds') }}
