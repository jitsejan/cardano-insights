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

filtered as (
    select
        repository,
        case
            when repository = 'input-output-hk/lace' then 'lace'
            when repository in (select repository from top_10) then 'top_10'
            else null
        end as repo_group,
        date_trunc('month', closed_at) as pr_month
    from base
    where repository = 'input-output-hk/lace' or repository in (select repository from top_10)
)

select
    repository,
    repo_group,
    pr_month,
    count(*) as feature_pr_count
from filtered
group by 1, 2, 3
order by 3, 1