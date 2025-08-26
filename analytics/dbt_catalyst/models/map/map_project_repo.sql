with manual as (
  select 
    cast(project_id as varchar) as project_id, 
    repo_key, 
    'seed' as source, 
    current_timestamp as mapped_at
  from {{ ref('map_repo_to_project') }}
),
auto as (
  -- Extract GitHub links from proposal data and convert to repo_key format
  select 
    cast(id as varchar) as project_id,
    lower(
      case 
        when website like '%github.com%' then 
          regexp_extract(website, 'github\.com/([^/]+/[^/]+)', 1)
        when link like '%github.com%' then
          regexp_extract(link, 'github\.com/([^/]+/[^/]+)', 1)
        when ideascale_link like '%github.com%' then
          regexp_extract(ideascale_link, 'github\.com/([^/]+/[^/]+)', 1)
      end
    ) as repo_key,
    'discovered' as source,
    _loaded_at as mapped_at
  from {{ ref('stg_proposals') }}
  where (website like '%github.com%' or link like '%github.com%' or ideascale_link like '%github.com%') 
)
select * from manual
union all
select * from auto
where repo_key is not null and repo_key != ''