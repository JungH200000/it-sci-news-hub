-- 008_unified_thumbnail.sql
-- weekly_articles에 새로 추가한 thumbnail column을 unified_articles view와 search_unified RPC에 추가

begin;

-- 1) 기존 함수 제거 (정확한 시그니처 명시)
drop function if exists public.search_unified(text, text, interval, integer);

-- 2) 기존 뷰 제거
--   다른 객체가 뷰를 참조하면 여기서 실패할 수 있음.
--   그런 경우에는 CASCADE를 쓰지 말고, 참조 객체를 먼저 수정하세요.
drop view if exists public.unified_articles;

-- 3) 새 뷰 생성 (열 이름을 명시해서 안전하게 고정)
create view public.unified_articles (
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
  tsv,
  thumbnail
) as
select
  'daily'::text as kind,
  date as date_key,
  null::text as week_key,
  published_at as sort_time,
  published_at,
  null::text as period_label,
  id,
  source,
  title,
  summary,
  link,
  category,
  tsv,
  thumbnail
from public.daily_articles
union all
select
  'weekly'::text as kind,
  null::date as date_key,
  week as week_key,
  coalesce(created_at, now()) as sort_time,
  null::timestamptz as published_at,
  period_label,
  id,
  source,
  title,
  summary,
  link,
  category,
  tsv,
  thumbnail
from public.weekly_articles;

-- 4) 새 함수 생성 (RETURNS TABLE에 thumbnail 포함)
create function public.search_unified(
  q text, -- 검색어
  cat text default null, -- 카테고리
  d_since interval default '14 days', -- 최근 n일 같은 기간 제한
  max_results int default 50 -- 한 종류 당 최대 결과 수
) returns table ( -- 검색 파라미터를 받어 결과를 table 형태로 반환
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
  thumbnail text,
  rank float -- 검색 점수로 높을수록 검색어와 더 잘 맞음
) language sql
  set search_path = public -- search_path를 pubilc으로 고정하여 public schema에서만 해석되도록 
as $$ -- 본문 sql 시작
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
      ua.thumbnail,
      ts_rank(ua.tsv, params.tsq) as rank, -- tsv와 검색어 tsq의 일치 정도를 점수로 환산
      row_number() over (
        partition by ua.kind
        order by ts_rank(ua.tsv, params.tsq) desc, ua.sort_time desc
      ) as rn
    from public.unified_articles ua -- unified_articles에서 기사 행을 가져와서 
    cross join params -- 위에서 만든 params와 모든 행을 결합해, 아래의 조건식에서 `params.tsq`와 `params.raw_q`를 사용할 수 있게 한다.
    where params.raw_q <> '' -- 빈 검색어면 결과 x
      and ua.tsv @@ params.tsq -- FTS 매치(인덱스 사용) -> 검색어에 맞는 기사만
      and (ua.kind <> 'daily' or ua.date_key >= current_date - coalesce(d_since, '14 days'::interval)) -- daily가 아닐 때는 그냥 통과, daily면 뒤의 조건 통과
      and (nullif(cat, '') is null or ua.category = cat)
  )
  -- 최종 결과 선택 및 정렬
  select
    kind, date_key, week_key, sort_time, published_at, period_label,
    id, source, title, summary, link, category, thumbnail, rank
  from filtered
  where rn <= case when max_results is null or max_results < 1 then 50 else max_results end
  order by kind, rank desc, sort_time desc;
$$;

-- 5) (옵션) 권한 재부여
-- grant execute on function public.search_unified(text, text, interval, integer) to anon, authenticated;

commit;
