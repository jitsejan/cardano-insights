with src as (
  select
    lower(replace(full_name, '/', '/')) as repo_key,
    id,
    full_name,
    name,
    description,
    created_at,
    updated_at,
    stargazers_count,
    forks_count,
    open_issues_count,
    default_branch,
    license
  from bronze.github_repos
)
select * from src