-- 002_indexes.sql

begin;

create extension if not exists pg_trgm;

create index if not exists idx_daily_date on public.daily_articles(date);
create index if not exists idx_daily_category on public.daily_articles(category);
create unique index if not exists uniq_daily_link on public.daily_articles(link);

create index if not exists idx_weekly_week on public.weekly_articles(week);
create unique index if not exists uniq_weekly_week_link on public.weekly_articles(week, link);

-- Trigram indexes for partial matching (PRD-8)
create index if not exists idx_daily_title_trgm on public.daily_articles using gin (title gin_trgm_ops);
create index if not exists idx_daily_summary_trgm on public.daily_articles using gin (summary gin_trgm_ops);
create index if not exists idx_weekly_title_trgm on public.weekly_articles using gin (title gin_trgm_ops);
create index if not exists idx_weekly_summary_trgm on public.weekly_articles using gin (summary gin_trgm_ops);

commit;
