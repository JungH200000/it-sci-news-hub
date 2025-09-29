-- 003_tsv_triggers.sql

begin;

alter table public.daily_articles add column if not exists tsv tsvector;
alter table public.weekly_articles add column if not exists tsv tsvector;

-- 기존 데이터에 tsv column(검색 column)을 채워줌
update public.daily_articles
set tsv = to_tsvector( -- to_tsvector : 텍스트를 검색용 토큰 집합으로 변경
  'simple',
  -- title + summary + category를 합쳐서 tsv column에 저장
  coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(category, '')
  -- coalesce(title, '') : title이 Null이면 빈 문자열로 변경
  -- || ' ' || : 문자열을 공백으로 이어 붙임
);

update public.weekly_articles
set tsv = to_tsvector(
  'simple',
  coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(category, '') || ' ' || coalesce(period_label, '')
);

-- trigger function 생성 - daily 전용
-- 새 행을 삽입하거나 기존 행을 수정할 때 자동 실행됨
create or replace function public.trg_daily_tsv_fn() returns trigger as $$
begin
  new.tsv := to_tsvector(
    'simple',
    coalesce(new.title, '') || ' ' || coalesce(new.summary, '') || ' ' || coalesce(new.category, '')
  );
  return new;
end
$$ language plpgsql;

-- daily_articles table에 trigger function 연결
drop trigger if exists trg_daily_tsv on public.daily_articles;
create trigger trg_daily_tsv
-- 데이터 삽입 or 수정 전에 실행되어 tsv를 항상 최신 상태로 유지
before insert or update on public.daily_articles
for each row execute function public.trg_daily_tsv_fn();

-- trigger function 생성 - weekly 전용(daily와 동일)
create or replace function public.trg_weekly_tsv_fn() returns trigger as $$
begin
  new.tsv := to_tsvector(
    'simple',
    coalesce(new.title, '') || ' ' || coalesce(new.summary, '') || ' ' || coalesce(new.category, '') || ' ' || coalesce(new.period_label, '')
  );
  return new;
end
$$ language plpgsql;

drop trigger if exists trg_weekly_tsv on public.weekly_articles;
create trigger trg_weekly_tsv
before insert or update on public.weekly_articles
for each row execute function public.trg_weekly_tsv_fn();

-- tsv column에 대해 GIN 인덱스를 만듦
-- GIN 인덱스는 Full Text Search에 최적화된 인덱스로, 특정 단어를 검색하면 모든 행을 일일이 스캔하지 않고 인덱스에서 바로 해당 기사 찾기 가능
create index if not exists idx_daily_tsv on public.daily_articles using gin(tsv);
create index if not exists idx_weekly_tsv on public.weekly_articles using gin(tsv);

commit;
