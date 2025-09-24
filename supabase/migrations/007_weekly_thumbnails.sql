-- 007_weekly_thumbnails.sql
-- Purpose: add optional thumbnail column for weekly articles (align with Daily card UI)
-- References: PRD-6.2, PRD-9.3, PRD-12-5

begin;

alter table if exists public.weekly_articles
  add column if not exists thumbnail text;

commit;
