with prs as (
  select
    lower(repository_full_name) as repo_key,
    date_trunc('month', merged_at) as month,
    count(*) as merged_prs
  from bronze.github_prs
  where merged_at is not null and merged = true
  group by 1,2
),
rels as (
  select
    lower(repository_full_name) as repo_key,
    date_trunc('month', published_at) as month,
    count(*) as releases
  from bronze.github_releases
  where published_at is not null and not draft and not prerelease
  group by 1,2
)
select
  coalesce(prs.repo_key, rels.repo_key) as repo_key,
  coalesce(prs.month, rels.month) as month,
  coalesce(prs.merged_prs, 0) as merged_prs,
  coalesce(rels.releases, 0) as releases
from prs
full outer join rels using (repo_key, month)