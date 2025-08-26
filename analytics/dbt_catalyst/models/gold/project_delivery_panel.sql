with repo_map as (
  select distinct project_id, repo_key
  from {{ ref('map_project_repo') }}
),
activity as (
  select rm.project_id, a.month, a.merged_prs, a.releases
  from {{ ref('fct_repo_activity_monthly') }} a
  join repo_map rm using (repo_key)
),
project_info as (
  select 
    cast(project_id as varchar) as project_id,
    title,
    amount_requested,
    funding_status,
    categories,
    has_github
  from {{ ref('stg_catalyst_proposal') }}
)
select 
  p.*,
  a.month,
  a.merged_prs,
  a.releases,
  case when a.month is not null then true else false end as has_activity_data
from project_info p
left join activity a using (project_id)