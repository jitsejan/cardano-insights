{% macro extract_github_org(repo_full_name) %}
  split_part({{ repo_full_name }}, '/', 1)
{% endmacro %}

{% macro extract_repo_name(repo_full_name) %}
  split_part({{ repo_full_name }}, '/', 2)  
{% endmacro %}

{% macro classify_pr_type(title) %}
  case
    when lower({{ title }}) like '%fix%' or lower({{ title }}) like '%bug%' then 'bug_fix'
    when lower({{ title }}) like '%feat%' or lower({{ title }}) like '%add%' then 'feature'
    when lower({{ title }}) like '%refactor%' then 'refactor'
    when lower({{ title }}) like '%test%' then 'test'
    when lower({{ title }}) like '%doc%' then 'documentation'
    else 'other'
  end
{% endmacro %}