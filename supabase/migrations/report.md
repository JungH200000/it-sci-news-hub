## `supabase db push` 후 WSL에서의 log

```
(.venv) jhpaxk02@DESKTOP-PREN5O4:~/it-sci-news-hub$ supabase db push
Initialising login role...
Connecting to remote database...
Skipping migration README.md... (file name must match pattern "<timestamp>_name.sql")
Do you want to push these migrations to the remote database?
 • 001_tables.sql
 • 002_indexes.sql
 • 003_tsv_triggers.sql
 • 004_views.sql
 • 005_search_rpc.sql

 [Y/n] Y
Applying migration 001_tables.sql...
Applying migration 002_indexes.sql...
Applying migration 003_tsv_triggers.sql...
NOTICE (00000): trigger "trg_daily_tsv" for relation "public.daily_articles" does not exist, skipping
NOTICE (00000): trigger "trg_weekly_tsv" for relation "public.weekly_articles" does not exist, skipping
Applying migration 004_views.sql...
Applying migration 005_search_rpc.sql...
Finished supabase db push.
```

---

## supabase - Advisors - security Advisor

### Errors

| name                   | title                  | level | facing   | categories   | description                                                                                                                                                                                         | detail                                                                         | remediation                                                                                | metadata                                                    | cache_key                                     |
| ---------------------- | ---------------------- | ----- | -------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------- | --------------------------------------------- |
| security_definer_view  | Security Definer View  | ERROR | EXTERNAL | ["SECURITY"] | Detects views defined with the SECURITY DEFINER property. These views enforce Postgres permissions and row level security policies (RLS) of the view creator, rather than that of the querying user | View \`public.unified_articles\` is defined with the SECURITY DEFINER property | https://supabase.com/docs/guides/database/database-linter?lint=0010_security_definer_view  | {"name":"unified_articles","type":"view","schema":"public"} | security_definer_view_public_unified_articles |
| rls_disabled_in_public | RLS Disabled in Public | ERROR | EXTERNAL | ["SECURITY"] | Detects cases where row level security (RLS) has not been enabled on tables in schemas exposed to PostgREST                                                                                         | Table \`public.daily_articles\` is public, but RLS has not been enabled.       | https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public | {"name":"daily_articles","type":"table","schema":"public"}  | rls_disabled_in_public_public_daily_articles  |
| rls_disabled_in_public | RLS Disabled in Public | ERROR | EXTERNAL | ["SECURITY"] | Detects cases where row level security (RLS) has not been enabled on tables in schemas exposed to PostgREST                                                                                         | Table \`public.weekly_articles\` is public, but RLS has not been enabled.      | https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public | {"name":"weekly_articles","type":"table","schema":"public"} | rls_disabled_in_public_public_weekly_articles |

---

### Warning

| name                         | title                        | level | facing   | categories   | description                                                   | detail                                                                              | remediation                                                                                      | metadata                                                         | cache_key                                                                              |
| ---------------------------- | ---------------------------- | ----- | -------- | ------------ | ------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| function_search_path_mutable | Function Search Path Mutable | WARN  | EXTERNAL | ["SECURITY"] | Detects functions where the search_path parameter is not set. | Function \`public.trg_daily_tsv_fn\` has a role mutable search_path                 | https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable | {"name":"trg_daily_tsv_fn","type":"function","schema":"public"}  | function_search_path_mutable_public_trg_daily_tsv_fn_e6e9edd8c1f2cf59bce9343cb2f70f20  |
| function_search_path_mutable | Function Search Path Mutable | WARN  | EXTERNAL | ["SECURITY"] | Detects functions where the search_path parameter is not set. | Function \`public.trg_weekly_tsv_fn\` has a role mutable search_path                | https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable | {"name":"trg_weekly_tsv_fn","type":"function","schema":"public"} | function_search_path_mutable_public_trg_weekly_tsv_fn_d9b7a67795c96cb98ec475e077171c10 |
| function_search_path_mutable | Function Search Path Mutable | WARN  | EXTERNAL | ["SECURITY"] | Detects functions where the search_path parameter is not set. | Function \`public.search_unified\` has a role mutable search_path                   | https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable | {"name":"search_unified","type":"function","schema":"public"}    | function_search_path_mutable_public_search_unified_fe17d6c8a4ad749485f15b3a56a10b34    |
| extension_in_public          | Extension in Public          | WARN  | EXTERNAL | ["SECURITY"] | Detects extensions installed in the \`public\` schema.        | Extension \`pg_trgm\` is installed in the public schema. Move it to another schema. | https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public          | {"name":"pg_trgm","type":"extension","schema":"public"}          | extension_in_public_pg_trgm                                                            |

## 수정

배포까지 염두에 둔다면 아래 두 가지는 최소한 수정 필요

1. **RLS 비활성(Errors)**

- `daily_articles`, `weekly_articles`가 public 스키마에 그대로 노출. 배포 환경에서 public 읽기/쓰기 권한을 안전하게 제어하려면 RLS를 켜고, 필요한 정책만 열어주는 게 기본.

- 작업 순서 예시:

```sql
alter table public.daily_articles enable row level security;
alter table public.weekly_articles enable row level security;
-- 그 뒤에 read-only 정책 등 필요한 정책 추가
```

2. **search_path 경고(Functions)**

- 트리거 함수와 `search_unified`가 현재 세션의 search_path에 의존하도록 되어 있어, 악의적 이용 가능성을 줄이려면 함수 정의에 `SET search_path`를 지정하는 게 안전.
- 예: `create or replace function ... set search_path = public;` 형태로 함수 헤더를 수정

나머지 항목(SECURITY DEFINER 뷰, pg_trgm 확장 위치)은 지금 단계에서 치명적이진 않지만, 앞의 두 부분은 배포 전에 정리하는 걸 추천.

=> `006_security_hardening.sql` 생성 후 migration

3. **security_definer_view**

- supabase의 autofix로 해결
