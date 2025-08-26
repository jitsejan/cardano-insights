{{
  config(
    materialized='table',
    description='Analysis of wallet ecosystem projects including Lace competitors'
  )
}}

with wallet_projects as (
    select
        p.*,
        f.title as fund_title,
        
        -- Enhanced wallet categorization
        case 
            when lower(title || ' ' || coalesce(solution, '')) like '%lace%' then 'lace'
            when lower(title || ' ' || coalesce(solution, '')) like '%yoroi%' then 'yoroi'
            when lower(title || ' ' || coalesce(solution, '')) like '%daedalus%' then 'daedalus'  
            when lower(title || ' ' || coalesce(solution, '')) like '%eternl%' then 'eternl'
            when lower(title || ' ' || coalesce(solution, '')) like '%nami%' then 'nami'
            when lower(title || ' ' || coalesce(solution, '')) like '%flint%' then 'flint'
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%browser wallet%', '%web wallet%', '%browser extension%'
            ]) then 'browser_wallet_generic'
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%mobile wallet%', '%mobile app%', '%ios%', '%android%'
            ]) then 'mobile_wallet_generic'
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%desktop wallet%', '%desktop app%'
            ]) then 'desktop_wallet_generic'
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%hardware wallet%', '%cold storage%', '%ledger%', '%trezor%'
            ]) then 'hardware_wallet_integration'
            else 'wallet_infrastructure'
        end as wallet_type,
        
        -- Competition level with Lace
        case
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%browser wallet%', '%web wallet%', '%browser extension wallet%'
            ]) then 'direct_competitor'
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%yoroi%', '%eternl%', '%nami%', '%flint%'
            ]) then 'existing_competitor'
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%mobile wallet%', '%desktop wallet%'
            ]) then 'indirect_competitor'
            when lower(title || ' ' || coalesce(solution, '')) like any(array[
                '%wallet integration%', '%wallet api%', '%wallet sdk%', '%wallet infrastructure%'
            ]) then 'ecosystem_enabler'
            else 'other'
        end as lace_competition_level

    from {{ ref('proposals_enriched') }} p
    left join {{ ref('stg_funds') }} f on p.fund_id = f.id
    where p.is_wallet_related = true
)

select
    id,
    title,
    fund_name,
    fund_title,
    wallet_type,
    lace_competition_level,
    funding_category,
    amount_requested,
    amount_received,
    funding_ratio,
    has_active_github,
    github_repo_count,
    github_links,
    approval_rate,
    primary_category,
    categories,
    
    -- Key project details
    problem,
    solution,
    website,
    
    -- Funding context
    fund_id,
    _loaded_at

from wallet_projects
order by 
    case lace_competition_level
        when 'direct_competitor' then 1
        when 'existing_competitor' then 2
        when 'indirect_competitor' then 3
        when 'ecosystem_enabler' then 4
        else 5
    end,
    amount_received desc