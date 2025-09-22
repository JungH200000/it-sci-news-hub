# `db/migrations`

DB 스키마·인덱스·뷰·RPC를 선언하는 SQL 스크립트 모음입니다. 각 파일은
PRD 요구사항(특히 PRD-6, PRD-8, PRD-16)을 충족하도록 순차 실행됩니다.

## 구조

| 파일 | 주요 내용 |
| --- | --- |
| `001_tables.sql` | `daily_articles`, `weekly_articles` 테이블 생성 |
| `002_indexes.sql` | 권장 인덱스 + `pg_trgm` 확장 + 유니크 제약 |
| `003_tsv_triggers.sql` | FTS용 `tsvector` 컬럼, 트리거 함수/GIN 인덱스 |
| `004_views.sql` | `unified_articles` 뷰 |
| `005_search_rpc.sql` | kind별 상한이 적용된 `search_unified` RPC |

각 스크립트는 트랜잭션으로 감싸져 있어 실패 시 롤백됩니다. idempotent 하게 작성되어, 여러 번 실행해도 안전합니다.

## 실행 예시

```bash
psql "$DATABASE_URL" -f db/migrations/001_tables.sql
psql "$DATABASE_URL" -f db/migrations/002_indexes.sql
psql "$DATABASE_URL" -f db/migrations/003_tsv_triggers.sql
psql "$DATABASE_URL" -f db/migrations/004_views.sql
psql "$DATABASE_URL" -f db/migrations/005_search_rpc.sql
```

`DATABASE_URL`은 `.env` 또는 `docs/env.md` 참고. Supabase 서비스 키를 사용할 때는 `psql "$(supabase db list --project-ref ...)"`처럼 래핑해도 됩니다.

## 검증 체크리스트

- `
  \d+ daily_articles`로 컬럼/인덱스 확인.
- `select * from pg_extension where extname = 'pg_trgm';`
- `select * from search_unified('AI');`로 FTS 섹션 캡 확인 (Daily/Weekly 각각 max 50).

문제가 생기면 트랜잭션이 자동으로 롤백되므로 수정 후 다시 실행하면 됩니다.
