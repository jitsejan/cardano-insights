{{ config(materialized='table') }}

-- Graph-ready dataset for Catalyst funding visualization
WITH fund_results AS (
    SELECT * FROM {{ ref('stg_fund_results') }}
),

-- Parse ADA amounts from different formats
funding_amounts AS (
    SELECT *,
        CASE 
            -- For funds 10+: Parse ADA amounts (â³197,850)
            WHEN raw_data__requested_ada IS NOT NULL 
                THEN TRY_CAST(REGEXP_REPLACE(REGEXP_REPLACE(raw_data__requested_ada, '[â³₳,]', '', 'g'), '[^0-9]', '', 'g') AS INTEGER)
            -- For funds 2-9: Convert USD to ADA (historical rate ~3 ADA per USD)
            WHEN raw_data__requestedxx IS NOT NULL 
                THEN TRY_CAST(CAST(REGEXP_REPLACE(REGEXP_REPLACE(raw_data__requestedxx, '[\$,]', '', 'g'), '[^0-9.]', '', 'g') AS DECIMAL(10,2)) * 3 AS INTEGER)
            ELSE 0
        END as amount_ada
    FROM fund_results
),

-- Extract company names from project titles
company_extraction AS (
    SELECT *,
        CASE 
            WHEN raw_data__proposal LIKE '%:%' 
                THEN TRIM(SPLIT_PART(raw_data__proposal, ':', 1))
            WHEN raw_data__proposal LIKE '% - %' 
                THEN TRIM(SPLIT_PART(raw_data__proposal, ' - ', 1))
            WHEN LOWER(raw_data__proposal) LIKE '%mlabs%' THEN 'MLabs'
            WHEN LOWER(raw_data__proposal) LIKE '%txpipe%' THEN 'TxPipe' 
            WHEN LOWER(raw_data__proposal) LIKE '%sundae labs%' THEN 'Sundae Labs'
            WHEN LOWER(raw_data__proposal) LIKE '%gimbalabs%' THEN 'Gimbalabs'
            WHEN LOWER(raw_data__proposal) LIKE '%sidan%' THEN 'SIDAN'
            WHEN LOWER(raw_data__proposal) LIKE '%anastasia labs%' THEN 'Anastasia Labs'
            WHEN LOWER(raw_data__proposal) LIKE '%hlabs%' THEN 'Hlabs'
            WHEN LOWER(raw_data__proposal) LIKE '%liqwid%' THEN 'Liqwid'
            WHEN LOWER(raw_data__proposal) LIKE '%mesh%' THEN 'Mesh'
            WHEN LOWER(raw_data__proposal) LIKE '%cardano%' THEN 'Cardano'
            ELSE LEFT(raw_data__proposal, 30)
        END as company
    FROM funding_amounts
),

-- Categorize projects
final_dataset AS (
    SELECT 
        fund_number as funding_round,
        raw_data__proposal as project_name,
        amount_ada,
        CASE 
            WHEN LOWER(raw_data__proposal) LIKE '%wallet%' THEN 'Wallet'
            WHEN LOWER(raw_data__proposal) SIMILAR TO '%defi%|%dex%|%swap%' THEN 'DeFi'
            WHEN LOWER(raw_data__proposal) SIMILAR TO '%nft%|%art%|%collectible%' THEN 'NFT/Art'
            WHEN LOWER(raw_data__proposal) SIMILAR TO '%education%|%community%|%outreach%' THEN 'Education/Community'
            WHEN LOWER(raw_data__proposal) SIMILAR TO '%infrastructure%|%tool%|%sdk%|%api%|%node%' THEN 'Infrastructure/Tools'
            ELSE 'Other'
        END as category,
        company,
        funding_decision,
        dbt_processed_at
    FROM company_extraction
)

SELECT *
FROM final_dataset
WHERE amount_ada > 0 
  AND project_name IS NOT NULL
  AND funding_round BETWEEN 2 AND 13
ORDER BY funding_round, amount_ada DESC