{{
  config(
    materialized='table',
    description='Staging layer for Catalyst proposals from Lido API'
  )
}}

select
    -- Identifiers
    id,
    user_id,
    fund_id,
    fund_name,
    campaign_id,
    campaign_name,
    ideascale_id,
    
    -- Basic info
    title,
    website,
    ideascale_link,
    ideascale_user,
    
    -- Content
    problem,
    solution,
    experience,
    
    -- Funding details
    amount_requested,
    currency,
    currency_symbol,
    project_status,
    funding_status,
    
    -- Voting metrics
    average_rating,
    yes_votes_count,
    no_votes_count,
    unique_wallets as unique_wallets_voted,
    
    -- Scores
    ranking_total,
    ca_rating,
    
    -- Links (raw - to be processed in silver)  
    link,
    
    -- Metadata
    type as proposal_type,
    _dlt_load_id as _loaded_at,
    'lido_api' as _source

from bronze.catalyst_proposals