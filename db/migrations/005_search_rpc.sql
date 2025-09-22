-- 005_search_rpc.sql
-- Reference: PRD-16 (search_unified RPC with section caps)

begin;

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
  id text,
  source text,
  title text,
  summary text,
  link text,
  category text,
  rank float
) language sql as $$
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
      and (cat is null or ua.category = cat)
  )
  select
    kind,
    date_key,
    week_key,
    sort_time,
    id,
    source,
    title,
    summary,
    link,
    category,
    rank
  from filtered
  where rn <= coalesce(nullif(max_results, 0), 50)
  order by kind, rank desc, sort_time desc;
$$;

commit;
