select
  id as project_id,
  title,
  problem,
  solution,
  experience,
  amount_requested,
  fund_id,
  fund_name,
  user_id,
  ideascale_id,
  project_status,
  funding_status,
  yes_votes_count,
  no_votes_count,
  unique_wallets as unique_wallets_voted,
  ranking_total,
  ca_rating,
  website,
  link,
  ideascale_link,
  currency,
  currency_symbol,
  type as proposal_type,
  _dlt_load_id as _loaded_at,
  'lido_api' as _source,
  -- Derived fields for GitHub analysis
  case when (website like '%github.com%' or link like '%github.com%' or ideascale_link like '%github.com%') then true else false end as has_github,
  '[]' as github_links,  -- placeholder, we'll extract from text in silver layer
  '[]' as categories,    -- placeholder, we'll categorize in silver layer  
  null as primary_category
from bronze.catalyst_proposals