{{
  config(
    materialized='table',
    description='Enriched proposals with categorization and GitHub analysis'
  )
}}

with base as (
    select * from {{ ref('stg_proposals') }}
),

enriched as (
    select
        *,
        
        -- Funding status categorization
        case
            when amount_received > 0 then 'funded'
            when funding_status in ('completed', 'approved') then 'approved'
            when funding_status in ('in_progress', 'pending') then 'in_progress'
            else 'not_funded'
        end as funding_category,
        
        -- Success metrics
        case when amount_received > 0 then amount_received / nullif(amount_requested, 0) else 0 end as funding_ratio,
        
        -- Voting engagement
        (yes_votes_count + no_votes_count + abstain_votes_count) as total_votes,
        case 
            when (yes_votes_count + no_votes_count + abstain_votes_count) > 0 
            then yes_votes_count::float / (yes_votes_count + no_votes_count + abstain_votes_count) 
            else null 
        end as approval_rate,
        
        -- GitHub activity indicator
        case when has_github and array_length(github_links, 1) > 0 then true else false end as has_active_github,
        array_length(github_links, 1) as github_repo_count,
        
        -- Wallet ecosystem detection
        case when (
            lower(title || ' ' || coalesce(problem, '') || ' ' || coalesce(solution, '')) like any(array[
                '%wallet%', '%lace%', '%yoroi%', '%daedalus%', '%eternl%', '%nami%', '%flint%',
                '%browser extension%', '%mobile wallet%', '%desktop wallet%', '%hardware wallet%',
                '%cardano wallet%', '%ada wallet%'
            ])
        ) then true else false end as is_wallet_related,
        
        -- Competition with Lace detection (more specific)
        case when (
            lower(title || ' ' || coalesce(problem, '') || ' ' || coalesce(solution, '')) like any(array[
                '%browser wallet%', '%web wallet%', '%browser extension wallet%',
                '%lace competitor%', '%lace alternative%', '%wallet competition%',
                '%yoroi%', '%eternl%', '%nami%', '%flint%'
            ])
        ) then true else false end as potential_lace_competitor

    from base
)

select * from enriched