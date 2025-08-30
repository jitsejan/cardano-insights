with base as (
    select
        repository,
        cast(closed_at as timestamp) as closed_at
    from {{ ref('stg_pull_requests') }}
    where lower(feat_classifier) = 'feature'
),

top_10 as (
    select repository
    from base
    group by 1
    order by count(*) desc
    limit 10
),

ranked as (
    select
        repository,
        closed_at,
        lag(closed_at) over (partition by repository order by closed_at) as prev_date
    from base
    where repository = 'input-output-hk/lace' or repository in (select repository from top_10)
),

intervals as (
    select
        repository,
        (extract('epoch' from closed_at) - extract('epoch' from prev_date)) / 86400.0 as days_diff
    from ranked
    where prev_date is not null
)

select
    repository,
    round(quantile_cont(days_diff, 0.5), 2) as median_days_between_feature_prs
from intervals
group by repository
order by median_days_between_feature_prs