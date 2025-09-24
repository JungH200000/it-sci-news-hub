# `supabase/migrations`

DB 스키마·인덱스·뷰·RPC를 선언하는 SQL 스크립트 모음입니다. 각 파일은
PRD 요구사항(특히 PRD-6, PRD-8, PRD-16)을 충족하도록 순차 실행됩니다.

## 구조

| 파일                   | 주요 내용                                                   |
| ---------------------- | ----------------------------------------------------------- |
| `001_tables.sql`       | `daily_articles`, `weekly_articles` 테이블 생성             |
| `002_indexes.sql`      | 권장 인덱스 + `pg_trgm` 확장 + 유니크 제약                  |
| `003_tsv_triggers.sql` | FTS용 `tsvector` 컬럼, 트리거 함수/GIN 인덱스               |
| `004_views.sql`        | `unified_articles` 뷰 (`published_at`, `period_label` 포함) |
| `005_search_rpc.sql`   | kind별 상한이 적용된 `search_unified` RPC                   |
| `006_security_hardening.sql` | RLS 활성화 및 함수 `search_path` 고정                         |
| `007_weekly_thumbnails.sql`  | `weekly_articles` 썸네일 컬럼 추가                         |
| `008_unified_thumbnail.sql`  | `unified_articles` 뷰/`search_unified`에 썸네일 노출         |

각 스크립트는 트랜잭션으로 감싸져 있어 실패 시 롤백됩니다. idempotent 하게 작성되어, 여러 번 실행해도 안전합니다.

## 실행 예시

```bash
psql "$DATABASE_URL" -f supabase/migrations/001_tables.sql
psql "$DATABASE_URL" -f supabase/migrations/002_indexes.sql
psql "$DATABASE_URL" -f supabase/migrations/003_tsv_triggers.sql
psql "$DATABASE_URL" -f supabase/migrations/004_views.sql
psql "$DATABASE_URL" -f supabase/migrations/005_search_rpc.sql
psql "$DATABASE_URL" -f supabase/migrations/006_security_hardening.sql
psql "$DATABASE_URL" -f supabase/migrations/007_weekly_thumbnails.sql
psql "$DATABASE_URL" -f supabase/migrations/008_unified_thumbnail.sql
```

`DATABASE_URL`은 `.env` 또는 `docs/env.md` 참고. Supabase 서비스 키를 사용할 때는 `psql "$(supabase db list --project-ref ...)"`처럼 래핑해도 됩니다.

## 검증 체크리스트

- `
\d+ daily_articles`로 컬럼/인덱스 확인.
- `select * from pg_extension where extname = 'pg_trgm';`
- `select * from search_unified('AI');`로 FTS 섹션 캡 확인 (Daily/Weekly 각각 max 50).

문제가 생기면 트랜잭션이 자동으로 롤백되므로 수정 후 다시 실행하면 됩니다.

### 001_tables.sql

- 목적: 프로젝트에서 사용할 기본 테이블(daily_articles, weekly_articles) 생성.
  - daily_articles: 하루 단위 기사 저장
  - weekly_articles: 주 단위 기사 저장

```sql
create table if not exists public.daily_articles (
  id text primary key,                -- 고유 ID (문자열)
  date date not null,                 -- 기사 날짜
  source text not null,               -- 기사 출처 (언론사 등)
  title text not null,                -- 기사 제목
  summary text,                       -- 기사 요약 (옵션)
  link text not null,                 -- 기사 원문 링크
  published_at timestamptz,           -- 실제 기사 발행 시각
  category text,                      -- 카테고리(예: AI, 보안)
  thumbnail text,                     -- 썸네일 이미지 URL
  created_at timestamptz default now()-- 데이터가 DB에 들어온 시각 (자동 기록)
);
```

### 002_indexes.sql

- 목적: 검색/중복방지 성능을 높이는 index 추가
  - 책에 목차/색인 붙이는 작업. “카테고리별 찾아줘” → 바로 찾음.
  - “제목에 ‘AI’ 들어간 거 찾아줘” → 빠르게 찾을 수 있음.

```sql
create extension if not exists pg_trgm; -- 부분검색(유사검색) 확장 설치
```

- `idx_daily_date` → 날짜별 빠른 정렬/검색
- `idx_daily_category` → 카테고리별 빠른 검색
- `uniq_daily_link` → 같은 기사 링크가 중복 저장되지 않도록 보장
- `idx_daily_title_trgm`, `idx_daily_summary_trgm` → trigram 인덱스: 제목/요약에서 "부분 일치" 검색이 빠르게 되도록.

### 003_tsv_triggers.sql

- 목적: 검색 전용 컬럼(tsv) 자동 생성 → Full Text Search 기능 강화
  - 검색 전용 그림자 사본을 만들어 두는 것.
  - 검색할 때 원본 긴 글을 직접 뒤지지 않고, 검색용 사본(tsv) 만 확인하면 빠르게 결과가 나옴.

```sql
alter table public.daily_articles add column if not exists tsv tsvector;
```

- `tsv` = 검색용 버전의 텍스트 (단어들을 분석해서 저장)
- `update ... set tsv = to_tsvector(...)` → 기존 데이터도 변환
- `create trigger ...` → 새로운 데이터가 들어올 때마다 자동으로 tsv 업데이트

```sql
-- 예시
new.tsv := to_tsvector('simple', coalesce(new.title, '') || ' ' || coalesce(new.summary, ''));
```

- 새 행이 들어오면 제목(new.title)+요약(new.summary) 합쳐서 tsv로 변환해 저장.

### 004_views.sql

- 목적: daily + weekly를 합쳐서 한 번에 조회 가능한 뷰(view) 생성.
  - 두 상자(daily, weekly)를 하나의 큰 창문(view)으로 보여주는 것.
  - 프론트엔드에서는 하루/주간 구분 안 하고 그냥 기사 목록 출력할 때 유용.
  - view가 없다면 `select ... from daily_articles ...`하고 `select ... from weekly_articles ...`을 해서 두 쿼리를 합치고 정렬해야함으로 코드가 복잡해짐.

```sql
create or replace view public.unified_articles as
select ... from public.daily_articles
union all
select ... from public.weekly_articles;
```

- kind 필드로 구분 (daily, weekly)
- 공통 필드(title, summary, link 등)만 뽑아서 합침
- 실제 데이터는 각각의 테이블에 있고, 이 뷰는 읽기 전용 가상 테이블

### 005_search_rpc.sql

- 목적: 사용자 검색 요청을 처리하는 검색 함수 제공.
  - “AI 관련 기사 최근 2주치 30개만 주세요” → 바로 이 함수 호출.
  - 프론트엔드에서 DB를 직접 복잡하게 쿼리할 필요 없이, 이 함수를 호출만 하면 됨.

```sql
create or replace function public.search_unified(
  q text,              -- 검색 키워드
  cat text default null,-- 카테고리 필터
  d_since interval default '14 days', -- 최근 N일 제한
  max_results int default 50          -- 최대 결과 수
)
```

- `ts_rank` → 검색어와 얼마나 잘 맞는지 점수 매김
- `row_number() over (partition by ua.kind)` → daily/weekly 각각에서 순번 매기기
- 조건
  - 검색어가 없으면 결과 없음
  - `cat` 있으면 해당 카테고리만
  - daily는 기본적으로 최근 14일만 검색

### 006_security_hardening.sql

- 목적: 공개 스키마 기본 보안을 강화.
  - `daily_articles`, `weekly_articles`에 RLS를 활성화하고 읽기 전용 정책을 적용.
  - 트리거 및 SQL 함수에 `set search_path = public`을 지정해 실행 컨텍스트를 고정.

### 007_weekly_thumbnails.sql

- 목적: Weekly 카드에서도 썸네일을 활용할 수 있도록 `weekly_articles`에 `thumbnail` 텍스트 컬럼을 추가.
- 기존 행과 호환되도록 nullable + idempotent로 작성.

### 008_unified_thumbnail.sql

- 목적: 검색/통합 뷰가 썸네일을 포함해 프런트 카드 UI에 바로 전달되도록 뷰와 RPC를 재정의.
- `search_unified`가 Daily/Weekly 각각의 썸네일을 반환함.

### 전체 요약

1. 001_tables.sql → 기사 상자(daily, weekly 테이블) 만들기
2. 002_indexes.sql → 빠른 검색용 목차/색인 달기
3. 003_tsv_triggers.sql → 검색 전용 사본(tsv) 자동 생성하기
4. 004_views.sql → daily+weekly 합친 가상 테이블(unified_articles)
5. 005_search_rpc.sql → 검색 함수(search_unified) 제공
6. 006_security_hardening.sql → RLS/함수 search_path 기본값 강화
7. 007_weekly_thumbnails.sql → Weekly 썸네일 컬럼 추가
8. 008_unified_thumbnail.sql → 통합 뷰/검색 RPC에 썸네일 노출

👉 그림으로 비유하면:
상자를 만들고(001)
목차를 붙이고(002)
검색용 사본을 만들고(003)
두 상자를 합쳐 보여주는 창문을 만들고(004)
검색 API를 제공한다(005).
