with feature_prs as (
  select
    repository,
    date_trunc('month', closed_at::timestamp) as month
  from {{ ref('stg_pull_requests') }}
  where lower(feat_classifier) = 'feature'
)

select
  repository,
  month,
  count(*) as feature_pr_count
from feature_prs
group by repository, month
order by repository, month