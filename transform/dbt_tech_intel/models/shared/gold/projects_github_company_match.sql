{{ config(materialized='table') }}

-- Gold: All proposals (funded + unfunded) with GitHub company-level matching
-- Links Catalyst projects to GitHub repos by organization/company
WITH all_proposals_with_github AS (
    SELECT 
        fund_number,
        official_project_name,
        lido_project_name,
        official_decision,
        official_ada_requested,
        lido_amount_requested,
        website,
        match_quality,
        
        -- Extract GitHub org/company from website URLs
        CASE 
            WHEN website LIKE '%github.com/%' THEN 
                SPLIT_PART(REGEXP_EXTRACT(website, 'github\.com/([^/?#]+/[^/?#]+)', 1), '/', 1)
            ELSE NULL
        END as github_org,
        
        -- Extract full repo name
        CASE 
            WHEN website LIKE '%github.com/%' THEN 
                REGEXP_EXTRACT(website, 'github\.com/([^/?#]+/[^/?#]+)', 1)
            ELSE NULL
        END as github_repo,
        
        processed_at
        
    FROM {{ ref('unified_proposals') }}
    WHERE website LIKE '%github%'
),

-- Get GitHub orgs from our tracked repositories
github_orgs AS (
    SELECT DISTINCT
        SPLIT_PART(full_name, '/', 1) as org_name,
        full_name,
        stargazers_count,
        forks_count,
        language as primary_language,
        created_at as repo_created_at,
        updated_at as repo_last_updated
    FROM {{ source('github', 'stg_github_repositories') }}
),

-- Company-level matching
company_matched AS (
    SELECT 
        p.*,
        g.org_name as matched_github_org,
        g.full_name as matched_repo_example,
        g.stargazers_count,
        g.forks_count,
        g.primary_language,
        g.repo_created_at,
        
        -- Match types
        CASE 
            WHEN p.github_repo = g.full_name THEN 'exact_repo_match'
            WHEN p.github_org = g.org_name THEN 'company_match'
            ELSE 'no_match'
        END as match_type
        
    FROM all_proposals_with_github p
    LEFT JOIN github_orgs g 
        ON p.github_org = g.org_name OR p.github_repo = g.full_name
)

SELECT 
    fund_number,
    official_project_name,
    official_decision,
    official_ada_requested,
    github_org,
    github_repo,
    matched_github_org,
    matched_repo_example,
    match_type,
    stargazers_count,
    forks_count,
    primary_language,
    website,
    match_quality as proposal_match_quality,
    
    -- Analysis categories
    CASE 
        WHEN official_decision = 'FUNDED' AND match_type = 'exact_repo_match' THEN 'funded_tracked_repo'
        WHEN official_decision = 'FUNDED' AND match_type = 'company_match' THEN 'funded_tracked_company'
        WHEN official_decision = 'FUNDED' THEN 'funded_untracked'
        WHEN match_type = 'exact_repo_match' THEN 'unfunded_tracked_repo'
        WHEN match_type = 'company_match' THEN 'unfunded_tracked_company'
        ELSE 'unfunded_untracked'
    END as funding_github_category,
    
    current_timestamp as analyzed_at
    
FROM company_matched
ORDER BY 
    CASE WHEN official_decision = 'FUNDED' THEN 0 ELSE 1 END,
    CASE WHEN match_type = 'exact_repo_match' THEN 0 
         WHEN match_type = 'company_match' THEN 1 
         ELSE 2 END,
    fund_number