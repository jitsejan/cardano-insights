{{ config(materialized='table') }}

-- Unified proposals combining official Catalyst results with Lido enrichment data
-- Links official funding decisions with Lido community data
WITH official_proposals AS (
    SELECT 
        fund_number,
        proposal_id,
        project_name,
        funding_decision,
        raw_data__requested_ada,
        raw_data__requestedxx,
        -- Standardize proposal name for matching
        LOWER(TRIM(raw_data__proposal)) as proposal_key
    FROM {{ ref('stg_fund_results') }}
),

lido_proposals AS (
    SELECT
        fund_id,
        fund_name,
        id as lido_proposal_id,
        title,
        project_status,
        funding_status,
        amount_requested,
        ideascale_link,
        website,
        -- Standardize title for matching  
        LOWER(TRIM(title)) as proposal_key
    FROM {{ ref('stg_proposals') }}
),

-- Join official results with Lido enrichment
unified AS (
    SELECT 
        o.fund_number,
        o.proposal_id,
        o.project_name as official_project_name,
        l.title as lido_project_name,
        o.funding_decision as official_decision,
        l.funding_status as lido_status,
        l.project_status as lido_project_status,
        
        -- Financial data
        o.raw_data__requested_ada as official_ada_requested,
        l.amount_requested as lido_amount_requested,
        
        -- Enrichment data from Lido
        l.ideascale_link,
        l.website,
        l.lido_proposal_id,
        
        -- Match quality
        CASE 
            WHEN o.proposal_key = l.proposal_key THEN 'exact'
            WHEN o.proposal_key LIKE '%' || l.proposal_key || '%' THEN 'partial'
            WHEN l.proposal_key LIKE '%' || o.proposal_key || '%' THEN 'partial'
            ELSE 'no_match'
        END as match_quality,
        
        current_timestamp as processed_at
        
    FROM official_proposals o
    FULL OUTER JOIN lido_proposals l 
        ON 'Fund ' || o.fund_number = l.fund_name
        AND (
            o.proposal_key = l.proposal_key OR
            o.proposal_key LIKE '%' || l.proposal_key || '%' OR 
            l.proposal_key LIKE '%' || o.proposal_key || '%'
        )
)

SELECT * FROM unified
ORDER BY fund_number, match_quality, official_project_name