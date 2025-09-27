# 📑 Product Requirements Document DEV (PRD_dev)

<!-- PRD-1 -->

## 1. 개요

<!-- PRD-1-1 -->

**프로젝트명**: IT/과학 뉴스 모아보기 & 요약 웹앱

<!-- PRD-1-2 -->

**기간**: 2주 (개인 프로젝트, MVP 개발)

<!-- PRD-1-3 -->

여러 매체의 IT·과학·기술 뉴스를 한 곳에서 날짜별·주차별로 모아 간단한 요약과 검색 기능으로 최신 동향을 빠르게 파악할 수 있는 서비스를 구축한다.

---

<!-- PRD-2 -->

## 2. 문제 정의

- 여러 뉴스 매체의 기사들을 한 곳에 모아서 정리된 정보를 전달하는 플랫폼의 부재
- 네이버 뉴스 경우 헤드라인 뉴스로 공통된 주제에 대한 여러 매체 기사 중 하나의 기사만 중점으로 보여줌
- IT/과학 분야 기사를 중립적으로 큐레이션해 모아 주는 전문 플랫폼이 부족하다.
- AI, 보안, 반도체 등 특정 주제·키워드 중심으로 뉴스를 선별해 보고 싶은 수요가 충족되지 않는다.

---

<!-- PRD-3 -->

## 3. 목표 사용자

<!-- PRD-3-1 -->

- 최신 IT/과학 뉴스를 빠르게 훑어보려는 일반 사용자

<!-- PRD-3-2 -->

- 기술 동향을 꾸준히 챙겨야 하는 학생·직장인

<!-- PRD-3-3 -->

- 특정 기술 키워드에 관심이 있는 개발자·연구자

---

<!-- PRD-4 -->

## 4. 핵심 가치

<!-- PRD-4-1 -->

- 날짜별(Daily)·주차별(Weekly)로 정리된 뉴스 피드

<!-- PRD-4-2 -->

- 기사 요약(2~3줄)로 빠른 이해

<!-- PRD-4-3 -->

- 키워드 검색과 카테고리 필터 제공

<!-- PRD-4-4 -->

- 원문 링크를 통한 심화 탐색

---

<!-- PRD-5 -->

## 5. MVP 범위

<!-- PRD-5-1 -->

- **Daily IT/Science 피드**: 한국경제 IT, DataNet RSS 소스를 자동 수집 (ZDNet Korea, ScienceDaily 연동은 확장 대상)

<!-- PRD-5-2 -->

- **Weekly SciTech 피드**: scienceON 주간 뉴스 스크래핑 결과 제공

<!-- PRD-5-3 -->

- **자동 수집 배치**: Daily 1일 4회, Weekly 주 2회 GitHub Actions로 구동

<!-- PRD-5-4 -->

- **검색**: PostgreSQL FTS(`tsvector`) + `pg_trgm` 인덱스 조합

<!-- PRD-5-5 -->

- **UI**: 탭 기반 레이아웃, 날짜/주차 사이드바, 카드 뷰, `Load More` 버튼, 반응형 지원

---

<!-- PRD-6 -->

## 6. 후순위 및 제외 범위

<!-- PRD-6-1 -->

- 기사 본문을 임베딩(벡터화)하여 중복 기사를 묶고 LLM 기반 요약 품질 고도화 (현재는 규칙 기반 추출 요약)

<!-- PRD-6-2 -->

- Supabase Auth 기반 로그인과 북마크·즐겨찾기

<!-- PRD-6-3 -->

- 사용자별 키워드 추천 및 개인화 피드

<!-- PRD-6-4 -->

- 해외/비한글 소스 확대 및 다국어 대응

---

<!-- PRD-7 -->

## 7. 사용자 경험 (UX)

### 상단/공통

<!-- PRD-7-1 -->

- 좌측 로고/서비스명, 중앙 탭(Daily / Weekly), 우측 키워드 검색 입력 필드

<!-- PRD-7-2 -->

- 반응형: 데스크탑은 사이드바 + 2~3열 카드, 모바일은 사이드바 접힘 + 1열 카드

### Daily 탭

<!-- PRD-7-3 -->

- 사이드바: 최근 14일 날짜 (최신 항목 `New` 뱃지)

<!-- PRD-7-4 -->

- 기사 영역: 기본 10개 카드, `Load More` 클릭 시 10개씩 추가 노출

### Weekly 탭

<!-- PRD-7-5 -->

- 사이드바: 최근 8주 주차 (최신 항목 `New` 뱃지)

<!-- PRD-7-6 -->

- 기사 영역: 기본 10개 카드, `Load More`로 10개씩 추가

### 검색 결과

<!-- PRD-7-7 -->

- Daily(최근 14일) / Weekly 섹션 분리 표시

<!-- PRD-7-8 -->

- 각 섹션 기본 10개 카드, `Load More`로 추가 로딩

### Load More UX

<!-- PRD-7-9 -->

- 버튼 클릭 시 `disabled` 처리 + “Loading…” + 스피너

<!-- PRD-7-10 -->

- 응답이 10개 미만이면 버튼 대신 “No more results” 안내

### 접근성

<!-- PRD-7-11 -->

- 탭: WAI-ARIA 패턴 지원 (Arrow/Home/End 키 이동)

<!-- PRD-7-12 -->

- 버튼: `aria-busy`, `aria-live="polite"` 적용

<!-- PRD-7-13 -->

- Load More 이후 추가된 첫 카드에 포커스 이동

### 에러·빈 상태 UI

<!-- PRD-7-14 -->

- 빈 결과: “No results found”

<!-- PRD-7-15 -->

- 네트워크 오류: “Network error. Retry”

<!-- PRD-7-16 -->

- 썸네일 없음: 플레이스홀더 이미지 + 본문 영역 확장

<!-- PRD-7-17 -->

- 수집 실패: “일시적으로 로딩에 실패했습니다. 다시 시도해주세요.”

---

<!-- PRD-8 -->

## 8. 기능 요구사항 (Acceptance Criteria)

<!-- PRD-8-1 -->

- Daily 사이드바는 최근 14개의 서로 다른 날짜를 내림차순으로 노출한다.

<!-- PRD-8-2 -->

- 날짜 선택 시 최신순으로 10개의 기사를 보여주고, `Load More` 클릭 시 10개씩 추가된다.

<!-- PRD-8-3 -->

- Weekly 탭도 동일한 로직으로 주차 목록과 기사 목록을 노출한다.

<!-- PRD-8-4 -->

- 검색은 Daily(최근 14일)와 Weekly를 동시에 수행하고, 결과를 관련도 → 최신순으로 정렬해 섹션별로 표시한다.

<!-- PRD-8-5 -->

- 카드에는 제목·요약·출처·일시(또는 주차)·카테고리를 표시하며 제목 클릭 시 새 탭으로 원문을 연다.

---

<!-- PRD-9 -->

## 9. 비기능 요구사항 (NFR)

<!-- PRD-9-1 -->

- **성능**: 목록 API p95 < 500ms, 초기 카드 렌더링 FCP < 2.5s(데스크탑 기준)

<!-- PRD-9-2 -->

- **접근성**: 키보드 내비게이션과 ARIA 속성 준수

<!-- PRD-9-3 -->

- **안정성**: 소스 일부 실패 시에도 나머지 서비스 지속, 사용자에게 토스트 등으로 안내

<!-- PRD-9-4 -->

- **SEO/공유**: 기본 `<title>` 및 OG 메타 태그 (SSR 미도입 가정)

<!-- PRD-9-5 -->

- **보안**: Supabase 테이블에 RLS 적용, API 레이트 리미트(기본 120req/분)

---

<!-- PRD-10 -->

## 10. 데이터 및 검색 설계

### 데이터 구조

<!-- PRD-10-1 -->

**Daily Articles**

<!-- PRD-10-1a -->

| 필드         | 타입          | 설명                                           |
| ------------ | ------------- | ---------------------------------------------- |
| id           | text (PK)     | `SHA1(link)` 등의 고유 ID                      |
| date         | date          | YYYY-MM-DD (KST 버킷)                          |
| source       | text          | 출처 (예: 한국경제 IT)                         |
| title        | text          | 제목                                           |
| summary      | text          | 2~3줄 요약 (null 허용)                         |
| link         | text (unique) | 원문 링크                                      |
| published_at | timestamptz   | 원문 발행 시각 (UTC)                           |
| category     | text          | AI/보안/반도체/로봇/생명과학/IT/과학/기술/기타 |
| thumbnail    | text          | 썸네일 URL (선택)                              |
| created_at   | timestamptz   | 삽입 시각 (default now)                        |

<!-- PRD-10-2 -->

**권장 인덱스**

```sql
create index if not exists idx_daily_date on daily_articles(date);
create index if not exists idx_daily_category on daily_articles(category);
create unique index if not exists uniq_daily_link on daily_articles(link);
create index if not exists idx_daily_title_trgm on daily_articles using gin (title gin_trgm_ops);
create index if not exists idx_daily_summary_trgm on daily_articles using gin (summary gin_trgm_ops);
```

<!-- PRD-10-3 -->

**Weekly Articles**

<!-- PRD-10-3a -->

| 필드         | 타입        | 설명                           |
| ------------ | ----------- | ------------------------------ |
| id           | text (PK)   | `SHA1(source+week+title+link)` |
| week         | text        | YYYY-MM-N (예: 2025-09-3)      |
| period_label | text        | UI 표시용 (“2025년 9월 3주차”) |
| source       | text        | 원 출처 (예: 동아사이언스)     |
| title        | text        | 제목                           |
| summary      | text        | 요약                           |
| link         | text        | 원문 링크                      |
| category     | text        | 기본 `과학기술`                |
| thumbnail    | text        | 썸네일 URL (선택)              |
| created_at   | timestamptz | 삽입 시각 (default now)        |

```sql
create index if not exists idx_weekly_week on weekly_articles(week);
create index if not exists idx_weekly_title_trgm on weekly_articles using gin (title gin_trgm_ops);
create index if not exists idx_weekly_summary_trgm on weekly_articles using gin (summary gin_trgm_ops);
```

<!-- PRD-10-4 -->

- 두 테이블 모두 Row Level Security(RLS) 활성화 및 읽기 정책 적용 (006_security_hardening.sql).

<!-- PRD-10-5 -->

- `unified_articles` 뷰와 `search_unified` RPC는 Daily/Weekly를 통합해 검색/표시한다 (008_unified_thumbnail.sql 기준).

### 카테고리 분류 규칙

<!-- PRD-10-6 -->

**소스별 기본값**

<!-- PRD-10-6a -->

- 한국경제 IT → `IT/과학`

<!-- PRD-10-6b -->

- DataNet → `IT/과학`

<!-- PRD-10-6c -->

- ZDNet Korea → `IT/기술`

<!-- PRD-10-6d -->

- ScienceDaily → `과학`

<!-- PRD-10-6e -->

- scienceON → `과학기술`

<!-- PRD-10-7 -->

**제목 키워드 덮어쓰기**

<!-- PRD-10-7a -->

- `AI|인공지능|GPT|LLM|딥러닝` → `AI`

<!-- PRD-10-7b -->

- `보안|해킹|유출|취약|랜섬` → `보안`

<!-- PRD-10-7c -->

- `반도체|칩|파운드리` → `반도체`

<!-- PRD-10-7d -->

- `로봇|로보틱스` → `로봇`

<!-- PRD-10-7e -->

- `생명|제약|백신|유전체|미생물` → `생명과학`

<!-- PRD-10-8 -->

로직: 기본값 지정 후 제목 키워드가 있으면 해당 카테고리로 덮어쓴다.

### 검색 설계

<!-- PRD-10-9 -->

- **엔진**: PostgreSQL FTS (`tsvector` + `websearch_to_tsquery`)

<!-- PRD-10-10 -->

- **보완**: `pg_trgm` 인덱스로 국문 부분 일치/유사도 향상

<!-- PRD-10-11 -->

- **범위**: Daily = 최근 14일, Weekly = 전체

<!-- PRD-10-12 -->

- **정렬**: 관련도(`ts_rank`) → 최신(`sort_time`)

<!-- PRD-10-13 -->

- **반환**: Daily와 Weekly 섹션을 분리하고 각 섹션 최대 50건 상한 적용

```sql
create or replace view public.unified_articles as
select
  'daily'::text as kind,
  date as date_key,
  null::text as week_key,
  published_at as sort_time,
  published_at,
  null::text as period_label,
  id,
  source,
  title,
  summary,
  link,
  category,
  tsv,
  thumbnail
from public.daily_articles
union all
select
  'weekly'::text as kind,
  null::date as date_key,
  week as week_key,
  coalesce(created_at, now()) as sort_time,
  null::timestamptz as published_at,
  period_label,
  id,
  source,
  title,
  summary,
  link,
  category,
  tsv,
  thumbnail
from public.weekly_articles;

create or replace function public.search_unified(
  q text,
  cat text default null,
  d_since interval default '14 days',
  max_results int default 50
) returns table (
  kind text,
  date_key date,
  week_key text,
  sort_time timestamptz,
  published_at timestamptz,
  period_label text,
  id text,
  source text,
  title text,
  summary text,
  link text,
  category text,
  thumbnail text,
  rank float
) language sql
  set search_path = public
as $$
  with params as (
    select
      coalesce(nullif(trim(q), ''), '')::text as raw_q,
      websearch_to_tsquery('simple', coalesce(nullif(trim(q), ''), '')) as tsq
  ),
  filtered as (
    select
      ua.kind,
      ua.date_key,
      ua.week_key,
      ua.sort_time,
      ua.published_at,
      ua.period_label,
      ua.id,
      ua.source,
      ua.title,
      ua.summary,
      ua.link,
      ua.category,
      ua.thumbnail,
      ts_rank(ua.tsv, params.tsq) as rank,
      row_number() over (
        partition by ua.kind
        order by ts_rank(ua.tsv, params.tsq) desc, ua.sort_time desc
      ) as rn
    from public.unified_articles ua
    cross join params
    where params.raw_q <> ''
      and ua.tsv @@ params.tsq
      and (ua.kind <> 'daily' or ua.date_key >= current_date - coalesce(d_since, '14 days'::interval))
      and (nullif(cat, '') is null or ua.category = cat)
  )
  select
    kind, date_key, week_key, sort_time, published_at, period_label,
    id, source, title, summary, link, category, thumbnail, rank
  from filtered
  where rn <= case when max_results is null or max_results < 1 then 50 else max_results end
  order by kind, rank desc, sort_time desc;
$$;
```

---

<!-- PRD-11 -->

## 11. 데이터 수집 파이프라인

### 소스

<!-- PRD-11-1 -->

**Daily (RSS)**

<!-- PRD-11-1a -->

- 한국경제 IT: `https://www.hankyung.com/feed/it`

<!-- PRD-11-1b -->

- DataNet: `https://www.datanet.co.kr/rss/allArticle.xml`

<!-- PRD-11-1c -->

- ZDNet Korea: `https://feeds.feedburner.com/zdkorea` (확장 예정)

<!-- PRD-11-1d -->

- ScienceDaily: `https://www.sciencedaily.com/rss/top/science.xml` (확장 예정)

<!-- PRD-11-2 -->

**Weekly (스크래핑)**

<!-- PRD-11-2a -->

- scienceON: `https://scienceon.kisti.re.kr/trendPromo/PORTrendPromoList.do`

### 수집 방식

<!-- PRD-11-3 -->

- Python 스크립트(`services/ingest/*.py`)가 RSS/DOM 파싱 → 데이터 정규화 → Supabase REST API로 UPSERT

<!-- PRD-11-4 -->

- Daily: `hankyung_rss_scraper.py`, `datanet_scraper.py` → `run_ingest.py daily`

<!-- PRD-11-5 -->

- Weekly: `science_on_scraper.py` → `run_ingest.py weekly`

<!-- PRD-11-6 -->

- 요약: 규칙 기반 추출 요약 (2~3문장, 최대 180자, 실패 시 `summary = null`)

<!-- PRD-11-7 -->

- 카테고리: 소스 기본값 → 제목 키워드 덮어쓰기 로직 준수

### 스케줄링 & 자동화

<!-- PRD-11-8 -->

- GitHub Actions `.github/workflows/ingest-daily.yml`: UTC 21:00 / 03:00 / 09:00 / 15:00 (KST 06:00 / 12:00 / 18:00 / 24:00)

<!-- PRD-11-9 -->

- `.github/workflows/ingest-weekly.yml`: UTC 03:00 월·목 (KST 12:00 월요일·목요일)

<!-- PRD-11-10 -->

- 공통 환경 변수: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `TZ=Asia/Seoul`

<!-- PRD-11-11 -->

- 로컬 실행 예시: `python services/ingest/run_ingest.py daily --limit 50`

### 데이터 품질 & 예외 처리

<!-- PRD-11-12 -->

- 중복 제거: `id` 및 `link` 기반 UPSERT (`resolution=merge-duplicates`)

<!-- PRD-11-13 -->

- 타임존: `date`는 KST 버킷, `published_at`은 UTC 기준 저장

<!-- PRD-11-14 -->

- 본문 150자 미만 기사 제외, 요약 없음 시 UI 배지로 안내

---

<!-- PRD-12 -->

## 12. 배포·환경 변수 & 자동화 스크립트

```
apps/web/.env.local
  NEXT_PUBLIC_API_BASE_URL=

services/api/.env
  DATABASE_URL=
  SUPABASE_URL=
  SUPABASE_SERVICE_KEY=
  TZ=Asia/Seoul
  ALLOWED_ORIGINS=

services/ingest/.env
  SUPABASE_URL=
  SUPABASE_SERVICE_KEY=
  TZ=Asia/Seoul
```

```
package.json (root)
  "scripts": {
    "dev:web": "npm --workspace apps/web run dev",
    "dev:api": "npm --workspace services/api run dev",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "format": "prettier -w ."
  }
```

<!-- PRD-12-1 -->

- 프런트엔드 개발 서버: `npm run dev:web` (Next.js 3000)

<!-- PRD-12-2 -->

- API 서버: `npm run dev:api` (Express 4000, 기본 베이스 URL `http://localhost:4000/api`)

<!-- PRD-12-3 -->

- Python 의존성: `pip install -r requirement.txt`

---

<!-- PRD-13 -->

## 13. 데이터 보존 정책 (옵션)

```sql
-- Daily: 30일 이전 삭제
delete from daily_articles
where date < current_date - interval '30 days';

-- Weekly: 26주 이전 삭제 (created_at 기준)
delete from weekly_articles
where created_at < now() - interval '26 weeks';
```

---

<!-- PRD-14 -->

## 14. 로깅/분석 (선택)

<!-- PRD-14-1 -->

- 이벤트: `select_date`, `select_week`, `search_submit`, `load_more`, `open_link`

<!-- PRD-14-2 -->

- 속성: 검색어, 카테고리, 날짜/주차, 페이지, 결과 수

<!-- PRD-14-3 -->

- 활용: 페이지 사이즈/정렬/사이드바 UX 튜닝 근거 확보

---

<!-- PRD-15 -->

## 15. 리스크 & 대응

<!-- PRD-15-1 -->

- RSS/DOM 구조 변경 → 어댑터 모듈화, 실패 시 소스별 격리 로그

<!-- PRD-15-2 -->

- 과도한 호출/비용 → GitHub Actions 스케줄 최소화 + API `limit` 강제

<!-- PRD-15-3 -->

- 저작권/이용약관 → 원문 링크·출처 명시, 각 사이트 `robots.txt` 준수

<!-- PRD-15-4 -->

- 이미지/텍스트 재사용 이슈 → MVP 단계는 썸네일 선택적 사용, 상업화 시 라이선스 계약 또는 대체 이미지 전략 수립

<!-- PRD-15-5 -->

- GitHub Actions 스케줄은 best-effort → 다중 스케줄로 재시도 여유 확보

---

<!-- PRD-16 -->

## 16. 실행 로드맵 (2주)

- **W1**
  <!-- PRD-16-1 -->
  - 프로젝트 초기 세팅 (리포 구조, 브랜치 전략, ESLint/Prettier)

  <!-- PRD-16-2 -->
  - Mock 데이터 기반 UI 뼈대 구현 (레이아웃, 탭, 사이드바, 카드, 빈/로딩/에러 상태)

  <!-- PRD-16-3 -->
  - 접근성 패턴 검증 및 컴포넌트 단위 테스트 작성

- **W2**
  <!-- PRD-16-4 -->
  - Supabase DB 마이그레이션 실행 (001~008 순차 적용)

  <!-- PRD-16-5 -->
  - Daily/Weekly 수집 파이프라인 구축 및 샘플 적재 (`run_ingest.py` + GitHub Actions)

  <!-- PRD-16-6 -->
  - API ↔ DB 연동, 프런트엔드와 실제 데이터 통합, 검색 RPC 연결

  <!-- PRD-16-7 -->
  - 배포 및 환경 변수 구성, 모니터링/로그 확인 흐름 정리, README·운영 가이드 업데이트

---

<!-- PRD-17 -->

## 17. Tech Stack & Hosting

<!-- PRD-17-1 -->

- **Frontend**: Next.js (React) – Vercel 배포 예정, 접근성 중심 컴포넌트 구성

<!-- PRD-17-2 -->

- **Backend API**: Node.js + Express (Railway 등) – Controller → Service → Repository 계층, OpenAPI(`docs/openapi.yaml`) 기반 문서, `helmet`/`cors`/`compression`/`express-rate-limit`/`pino-http`

<!-- PRD-17-3 -->

- **Database**: Supabase(PostgreSQL) – SQL 마이그레이션으로 스키마/뷰/RPC 관리

<!-- PRD-17-4 -->

- **Batch/Ingest**: Python 스크립트 + GitHub Actions 스케줄러

<!-- PRD-17-5 -->

- **언어**: JavaScript(Next.js, Express), Python(수집) – 차후 TypeScript 확장 고려
