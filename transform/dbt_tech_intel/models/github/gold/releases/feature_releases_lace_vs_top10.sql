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

filtered as (
    select
        repository,
        case
            when repository = 'input-output-hk/lace' then 'lace'
            when repository in (select repository from top_10) then 'top_10'
            else null
        end as repo_group,
        date_trunc('month', published_at) as release_month
    from base
    where repository = 'input-output-hk/lace' or repository in (select repository from top_10)
)

select
    repository,
    repo_group,
    release_month,
    count(*) as feature_release_count
from filtered
group by 1, 2, 3
order by 2, 1