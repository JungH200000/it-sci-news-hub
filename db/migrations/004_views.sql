-- 004_views.sql
-- Reference: PRD-16 (unified_articles view)

begin;

create or replace view public.unified_articles as
select
  'daily'::text as kind,
  date as date_key,
  null::text as week_key,
  published_at as sort_time,
  id,
  source,
  title,
  summary,
  link,
  category,
  tsv
from public.daily_articles
union all
select
  'weekly'::text as kind,
  null::date as date_key,
  week as week_key,
  coalesce(created_at, now()) as sort_time,
  id,
  source,
  title,
  summary,
  link,
  category,
  tsv
from public.weekly_articles;

commit;
