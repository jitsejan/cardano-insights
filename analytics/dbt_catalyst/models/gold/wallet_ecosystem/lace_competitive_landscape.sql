{{
  config(
    materialized='table',
    description='Competitive landscape analysis specifically focused on Lace wallet ecosystem'
  )
}}

with lace_ecosystem as (
    select * from {{ ref('wallet_ecosystem_analysis') }}
),

competitive_analysis as (
    select
        lace_competition_level,
        wallet_type,
        
        -- Project counts
        count(*) as project_count,
        count(*) filter (where funding_category = 'funded') as funded_project_count,
        count(*) filter (where has_active_github) as projects_with_github,
        
        -- Funding analysis
        sum(case when funding_category = 'funded' then amount_received else 0 end) as total_funding_received,
        avg(case when funding_category = 'funded' then amount_received else null end) as avg_funding_per_funded_project,
        
        -- Success rates
        round(
            count(*) filter (where funding_category = 'funded')::numeric / 
            count(*)::numeric * 100, 1
        ) as funding_success_rate,
        
        round(
            count(*) filter (where has_active_github)::numeric / 
            count(*)::numeric * 100, 1
        ) as github_adoption_rate,
        
        -- Average scores
        round(avg(approval_rate) * 100, 1) as avg_approval_rate,
        round(avg(funding_ratio) * 100, 1) as avg_funding_ratio
        
    from lace_ecosystem
    group by lace_competition_level, wallet_type
),

project_examples as (
    select
        lace_competition_level,
        wallet_type,
        array_agg(
            json_build_object(
                'title', title,
                'funding_received', amount_received,
                'has_github', has_active_github,
                'github_repos', github_repo_count
            ) order by amount_received desc
        ) filter (where funding_category = 'funded') as top_funded_examples
    from lace_ecosystem
    group by lace_competition_level, wallet_type
)

select
    ca.*,
    pe.top_funded_examples,
    
    -- Strategic priority scoring (higher = more important to monitor)
    case ca.lace_competition_level
        when 'direct_competitor' then 100
        when 'existing_competitor' then 75
        when 'indirect_competitor' then 50
        when 'ecosystem_enabler' then 25
        else 10
    end + 
    case when ca.funding_success_rate > 50 then 20 else 0 end +
    case when ca.total_funding_received > 100000 then 15 else 0 end as strategic_priority_score

from competitive_analysis ca
left join project_examples pe 
    on ca.lace_competition_level = pe.lace_competition_level 
    and ca.wallet_type = pe.wallet_type

order by strategic_priority_score desc, total_funding_received desc