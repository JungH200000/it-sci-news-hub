-- 007_weekly_thumbnails.sql
-- thumbnail column을 weekly_articles table에 추가

begin;

alter table if exists public.weekly_articles
  add column if not exists thumbnail text;

commit;
