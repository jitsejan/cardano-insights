{{ config(materialized='table') }}

-- Stage official fund results from Google Sheets
SELECT 
    fund_number,
    proposal_id,
    raw_data__proposal as project_name,
    raw_data__requested_ada as requested_ada,
    raw_data__votes_cast as votes_cast,
    raw_data__yes as yes_votes_ada,
    raw_data__meets_approval_threshold as approval_status,
    raw_data__status as funding_status,
    extracted_at,
    'Fund ' || fund_number as fund_name,
    
    -- Raw data fields
    raw_data__proposal,
    raw_data__votes_cast,
    raw_data__yes,
    raw_data__abstain,
    raw_data__meets_approval_threshold,
    raw_data__requested_ada,
    raw_data__requestedxx,
    raw_data__status as funding_decision,
    raw_data__fund_depletion,
    raw_data__reason_for_not_funded_status,
    
    -- Metadata
    _dlt_load_id,
    _dlt_id,
    current_timestamp as dbt_processed_at
    
FROM {{ source('official', 'results') }}
WHERE raw_data__status = 'FUNDED'  -- Focus on funded projects