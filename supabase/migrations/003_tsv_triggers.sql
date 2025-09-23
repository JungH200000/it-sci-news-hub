-- 003_tsv_triggers.sql
-- References: PRD-8 (FTS requirements)

begin;

alter table public.daily_articles add column if not exists tsv tsvector;
alter table public.weekly_articles add column if not exists tsv tsvector;

update public.daily_articles
set tsv = to_tsvector(
  'simple',
  coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(category, '')
);

update public.weekly_articles
set tsv = to_tsvector(
  'simple',
  coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(category, '') || ' ' || coalesce(period_label, '')
);

create or replace function public.trg_daily_tsv_fn() returns trigger as $$
begin
  new.tsv := to_tsvector(
    'simple',
    coalesce(new.title, '') || ' ' || coalesce(new.summary, '') || ' ' || coalesce(new.category, '')
  );
  return new;
end
$$ language plpgsql;

drop trigger if exists trg_daily_tsv on public.daily_articles;
create trigger trg_daily_tsv
before insert or update on public.daily_articles
for each row execute function public.trg_daily_tsv_fn();

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

create index if not exists idx_daily_tsv on public.daily_articles using gin(tsv);
create index if not exists idx_weekly_tsv on public.weekly_articles using gin(tsv);

commit;
