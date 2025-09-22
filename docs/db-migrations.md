# DB Migration Policy

Reference: PRD-6, PRD-16

Order (idempotent, incremental)

1. 001_tables – daily/weekly tables
2. 002_indexes – listing/sort/unique/trgm indexes
3. 003_tsv_triggers – add `tsv` columns and triggers
4. 004_views – `unified_articles` view
5. 005_search_rpc – `search_unified` RPC (section caps)
(optional) 006_policies – RLS (read-only)
(optional) 007_retention_jobs – retention SQL

Notes

- Each step must not depend on later steps.
- Apply safely multiple times (IF NOT EXISTS, CREATE OR REPLACE).

## Execution checklist

- 환경 변수: `DATABASE_URL` (또는 `SUPABASE_URL`/`SUPABASE_SERVICE_KEY`).
- 적용 방법 예시

  ```bash
  psql "$DATABASE_URL" -f db/migrations/001_tables.sql
  psql "$DATABASE_URL" -f db/migrations/002_indexes.sql
  ...
  ```

- 모든 스크립트는 트랜잭션으로 래핑되어 실패 시 롤백됨.
- 적용 후 `select * from pg_extension where extname = 'pg_trgm';`로 확장 설치 확인.

## 객체 요약 (PRD 매핑)

- `daily_articles`, `weekly_articles` (PRD-6)
  - 기본 필드 + `created_at default now()`.
  - 일일/주간 고유 조건: `uniq_daily_link`, `uniq_weekly_week_link`.
- GIN 인덱스 (PRD-8)
  - `tsv` + `gin_trgm_ops` 인덱스로 부분 일치 보완.
- 트리거 함수 (PRD-8)
  - `trg_daily_tsv_fn`, `trg_weekly_tsv_fn`가 `tsvector` 갱신.
- `unified_articles` 뷰 (PRD-16)
  - Daily/Weekly를 단일 결과셋으로 제공.
- `search_unified` RPC (PRD-8, PRD-16)
  - `row_number()` 파티션으로 kind별 `max_results` 제한.
  - 파라미터: `q`, `cat`, `d_since`(기본 14일), `max_results`(기본 50).

## 사이드바 쿼리 예시 (PRD-12)

```sql
-- Daily 최근 14개 날짜
select distinct date
from daily_articles
order by date desc
limit 14;

-- Weekly 최근 8개 주차
select distinct week
from weekly_articles
order by week desc
limit 8;
```

## 성능 확인 가이드

- 샘플 데이터 적재 후 `EXPLAIN ANALYZE`로 주요 쿼리 측정.
- 목표: 목록/검색 쿼리 `p95 < 500ms` (PRD-13-1).
- 트리거/GIN 인덱스 적용 여부는 `
  \d+ daily_articles` 등으로 확인.
