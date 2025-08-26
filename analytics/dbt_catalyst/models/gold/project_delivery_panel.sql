with repo_map as (
  select distinct project_id, repo_key
  from {{ ref('map_project_repo') }}
),
github_repos_summary as (
  -- Direct access to GitHub data in bronze layer
  select 
    lower(full_name) as repo_key,
    count(*) as github_repos_count,
    max(created_at) as latest_repo_created,
    sum(stargazers_count) as total_stars,
    sum(forks_count) as total_forks
  from bronze.github_repos
  group by lower(full_name)
),
github_activity as (
  select 
    rm.project_id,
    gr.total_stars,
    gr.total_forks,
    gr.github_repos_count
  from repo_map rm
  left join github_repos_summary gr using (repo_key)
),
project_info as (
  select 
    cast(id as varchar) as project_id,
    title,
    amount_requested,
    funding_status,
    case when (website like '%github.com%' or link like '%github.com%' or ideascale_link like '%github.com%') then true else false end as has_github
  from {{ ref('stg_proposals') }}
)
select 
  p.*,
  coalesce(ga.total_stars, 0) as github_stars,
  coalesce(ga.total_forks, 0) as github_forks,
  coalesce(ga.github_repos_count, 0) as linked_repos_count,
  case when ga.project_id is not null then true else false end as has_github_data
from project_info p
left join github_activity ga using (project_id)