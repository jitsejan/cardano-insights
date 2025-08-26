with filtered as (
    select
        repository,
        cast(published_at as timestamp) as published_at
    from {{ ref('stg_releases') }}
)

select
    repository,
    date_trunc('month', published_at) as release_month,
    count(*) as feature_release_count
from filtered
group by 1, 2
order by 2, 1