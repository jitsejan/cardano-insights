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
    amount_received,
    currency,
    currency_symbol,
    project_status,
    funding_status,
    
    -- Voting metrics
    average_rating,
    yes_votes_count,
    no_votes_count,
    abstain_votes_count,
    unique_wallets as unique_wallets_voted,
    vote_casts,
    vote,
    
    -- Scores
    ranking_total,
    ca_rating,
    alignment_score,
    feasibility_score,
    auditability_score,
    
    -- Links (raw - to be processed in silver)
    embedded_uris,
    links,
    link,
    
    -- GitHub info (from enrichment)
    github_links,
    has_github,
    
    -- Categories (from enrichment)
    categories,
    primary_category,
    
    -- Metadata
    type as proposal_type,
    current_timestamp as _loaded_at,
    'lido_api' as _source

from {{ source('lido', 'proposals_enriched') }}