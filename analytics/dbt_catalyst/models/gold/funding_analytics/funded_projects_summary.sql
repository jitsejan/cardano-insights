{{
  config(
    materialized='table',
    description='Summary of successfully funded projects with key metrics'
  )
}}

with funded_projects as (
    select
        p.*,
        f.title as fund_title,
        f.funding_available as fund_total_available
    from {{ ref('proposals_enriched') }} p
    left join {{ ref('stg_funds') }} f on p.fund_id = f.id
    where p.funding_category = 'funded'
),

project_metrics as (
    select
        fund_id,
        fund_name,
        fund_title,
        
        -- Funding metrics
        count(*) as total_funded_projects,
        sum(amount_received) as total_funding_distributed,
        avg(amount_received) as avg_funding_per_project,
        median(amount_received) as median_funding_per_project,
        max(amount_received) as max_single_funding,
        
        -- Project characteristics
        count(*) filter (where has_active_github) as projects_with_github,
        count(*) filter (where is_wallet_related) as wallet_ecosystem_projects,
        count(*) filter (where potential_lace_competitor) as potential_lace_competitors,
        
        -- Category distribution
        count(*) filter (where 'DeFi' = any(string_to_array(replace(replace(categories, '[', ''), ']', ''), ','))) as defi_projects,
        count(*) filter (where 'Infrastructure' = any(string_to_array(replace(replace(categories, '[', ''), ']', ''), ','))) as infrastructure_projects,
        count(*) filter (where 'Developer Tools' = any(string_to_array(replace(replace(categories, '[', ''), ']', ''), ','))) as devtools_projects,
        
        -- Success metrics
        avg(approval_rate) as avg_approval_rate,
        avg(funding_ratio) as avg_funding_ratio

    from funded_projects
    group by fund_id, fund_name, fund_title
)

select
    *,
    -- Additional calculated metrics
    round(projects_with_github::numeric / total_funded_projects * 100, 1) as github_adoption_pct,
    round(wallet_ecosystem_projects::numeric / total_funded_projects * 100, 1) as wallet_ecosystem_pct,
    round(potential_lace_competitors::numeric / total_funded_projects * 100, 1) as lace_competition_pct

from project_metrics
order by fund_id desc