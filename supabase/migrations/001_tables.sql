-- 001_tables.sql
-- Reference: PRD-6 (Daily/Weekly schema)

begin;

create table if not exists public.daily_articles (
  id text primary key,
  date date not null,
  source text not null,
  title text not null,
  summary text,
  link text not null,
  published_at timestamptz,
  category text,
  thumbnail text,
  created_at timestamptz default now()
);

create table if not exists public.weekly_articles (
  id text primary key,
  week text not null,
  period_label text,
  source text not null,
  title text not null,
  summary text,
  link text not null,
  category text default '과학기술',
  created_at timestamptz default now()
);

commit;
