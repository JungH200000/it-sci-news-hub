-- 006_security_hardening.sql
-- Purpose: enable RLS on public tables and enforce stable search_path on functions

begin;

-- Enable Row Level Security and allow read-only access
alter table public.daily_articles enable row level security;
alter table public.weekly_articles enable row level security;

drop policy if exists daily_articles_read_policy on public.daily_articles;
create policy daily_articles_read_policy
  on public.daily_articles
  for select
  using (true);

drop policy if exists weekly_articles_read_policy on public.weekly_articles;
create policy weekly_articles_read_policy
  on public.weekly_articles
  for select
  using (true);

-- Ensure trigger functions run with a fixed search_path
create or replace function public.trg_daily_tsv_fn() returns trigger
  set search_path = public
as $$
begin
  new.tsv := to_tsvector(
    'simple',
    coalesce(new.title, '') || ' ' || coalesce(new.summary, '') || ' ' || coalesce(new.category, '')
  );
  return new;
end
$$ language plpgsql;

create or replace function public.trg_weekly_tsv_fn() returns trigger
  set search_path = public
as $$
begin
  new.tsv := to_tsvector(
    'simple',
    coalesce(new.title, '') || ' ' || coalesce(new.summary, '') || ' ' || coalesce(new.category, '') || ' ' || coalesce(new.period_label, '')
  );
  return new;
end
$$ language plpgsql;

-- Ensure SQL function uses stable search_path
create or replace function public.search_unified(
  q text,
  cat text default null,
  d_since interval default '14 days',
  max_results int default 50
) returns table (
  kind text,
  date_key date,
  week_key text,
  sort_time timestamptz,
  published_at timestamptz,
  period_label text,
  id text,
  source text,
  title text,
  summary text,
  link text,
  category text,
  rank float
) language sql
  set search_path = public
as $$
  with params as (
    select
      coalesce(nullif(trim(q), ''), '')::text as raw_q,
      websearch_to_tsquery('simple', coalesce(nullif(trim(q), ''), '')) as tsq
  ),
  filtered as (
    select
      ua.kind,
      ua.date_key,
      ua.week_key,
      ua.sort_time,
      ua.published_at,
      ua.period_label,
      ua.id,
      ua.source,
      ua.title,
      ua.summary,
      ua.link,
      ua.category,
      ts_rank(ua.tsv, params.tsq) as rank,
      row_number() over (
        partition by ua.kind
        order by ts_rank(ua.tsv, params.tsq) desc, ua.sort_time desc
      ) as rn
    from public.unified_articles ua
    cross join params
    where params.raw_q <> ''
      and ua.tsv @@ params.tsq
      and (ua.kind <> 'daily' or ua.date_key >= current_date - coalesce(d_since, '14 days'::interval))
      and (nullif(cat, '') is null or ua.category = cat)
  )
  select
    kind,
    date_key,
    week_key,
    sort_time,
    published_at,
    period_label,
    id,
    source,
    title,
    summary,
    link,
    category,
    rank
  from filtered
  where rn <= case when max_results is null or max_results < 1 then 50 else max_results end
  order by kind, rank desc, sort_time desc;
$$;

commit;
