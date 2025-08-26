{% macro to_repo_key(owner, repo) -%}
  lower(replace(replace(owner || '/' || repo, '.git', ''), ' ', ''))
{%- endmacro %}

{% macro month_bucket(ts_column) -%}
  date_trunc('month', {{ ts_column }})
{%- endmacro %}