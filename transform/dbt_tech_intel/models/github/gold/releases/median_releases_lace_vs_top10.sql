with base as (
    select
        repository,
        cast(published_at as timestamp) as published_at
    from {{ ref('stg_releases') }}
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
        published_at,
        case
            when repository = 'input-output-hk/lace' then 'lace'
            when repository in (select repository from top_10) then 'top_10'
            else null
        end as repo_group,
        lag(published_at) over (partition by repository order by published_at) as prev_date
    from base
    where repository = 'input-output-hk/lace' or repository in (select repository from top_10)
),

intervals as (
    select
        repository,
        (extract('epoch' from published_at) - extract('epoch' from prev_date)) / 86400.0 as days_diff
    from ranked
    where prev_date is not null
)

select
    repository,
    round(quantile_cont(days_diff, 0.5), 2) as median_days_between_releases
from intervals
group by repository
order by median_days_between_releases