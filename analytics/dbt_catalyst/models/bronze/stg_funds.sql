{{
  config(
    materialized='table',
    description='Staging layer for Catalyst funds from Lido API'
  )
}}

select
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
    current_timestamp as _loaded_at,
    'lido_api' as _source

from bronze.catalyst_funds