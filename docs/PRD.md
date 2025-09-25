# 📑 Product Requirements Document (PRD)

<!-- PRD-1 -->

## 1. 개요

**프로젝트명**: IT/과학 뉴스 모아보기 & 요약 웹앱
**기간**: 2주 (개인 프로젝트, MVP 개발)

여러 매체의 IT/과학/기술 뉴스를 한 곳에 모아 날짜별·주차별로 제공하고,
짧은 요약과 검색으로 사용자가 최신 동향을 **빠르게** 파악할 수 있게 한다.

---

<!-- PRD-2 -->

## 2. 문제 정의

<!-- PRD-2-1 -->

- 여러 매체를 일일이 돌며 뉴스를 확인하는 것은 번거롭다.

<!-- PRD-2-2 -->

- 최신 동향을 빠르게 확인하려 해도 광고·중복 기사로 비효율적이다.

<!-- PRD-2-3 -->

- 특정 주제(예: AI, 보안, 반도체)에 대한 기사만 모아보고 싶다.

---

<!-- PRD-3 -->

## 3. 목표 사용자

<!-- PRD-3-1 -->

- 최신 IT/과학 뉴스를 빠르게 확인하려는 일반인

<!-- PRD-3-2 -->

- 동향을 꾸준히 챙겨야 하는 학생·직장인

<!-- PRD-3-3 -->

- 특정 기술 키워드에 관심 있는 개발자·연구자

---

<!-- PRD-4 -->

## 4. 핵심 가치

<!-- PRD-4-1 -->

- 날짜별(Daily) / 주차별(Weekly)로 정리된 뉴스 피드

<!-- PRD-4-2 -->

- 기사 요약(2\~3줄)로 빠른 이해

<!-- PRD-4-3 -->

- 키워드 검색과 카테고리 필터

<!-- PRD-4-4 -->

- 원문 링크로 심화 탐색

---

<!-- PRD-5 -->

## 5. MVP 범위

<!-- PRD-5-1 -->

- **Daily IT/Science**: RSS (한국경제 IT, DataNet, ZDNet Korea, ScienceDaily)
  ※ 초기 개발은 한국경제 RSS로 시작했으며 현재 DataNet까지 자동화 완료 → 이후 소스 확장

<!-- PRD-5-2 -->

- **Weekly SciTech**: scienceON 주간 뉴스 스크래핑

<!-- PRD-5-3 -->

- **자동 수집**: Daily(매일 06:00 KST), Weekly(매주 월 08:00 KST)

<!-- PRD-5-4 -->

- **검색**: PostgreSQL FTS(tsvector) + `pg_trgm` 보완

<!-- PRD-5-5 -->

- **UI**: 탭 전환, 사이드바, 카드 뷰, **Load More 버튼**

<!-- PRD-5-6 -->

- **개인화(로그인/북마크)**: 제외(차후 확장)

---

<!-- PRD-6 -->

## 6. 데이터 구조

### Daily Articles

<!-- PRD-6.1-1 -->

| 필드         | 타입          | 설명                                           |
| ------------ | ------------- | ---------------------------------------------- |
| id           | text (PK)     | `SHA1(link)` 등 고유 ID                        |
| date         | date          | YYYY-MM-DD (KST 버킷)                          |
| source       | text          | 출처 (예: 한국경제 IT)                         |
| title        | text          | 제목                                           |
| summary      | text          | 2\~3줄 요약                                    |
| link         | text (unique) | 원문 링크                                      |
| published_at | timestamptz   | 원문 발행 시각(UTC ISO)                        |
| category     | text          | AI/보안/반도체/로봇/생명과학/IT/과학/기술/기타 |
| thumbnail    | text          | 썸네일 URL(선택)                               |
| created_at   | timestamptz   | 삽입 시각(default now)                         |

**권장 인덱스**

<!-- PRD-6.1-2 -->

```sql
create index if not exists idx_daily_date on daily_articles(date);
create index if not exists idx_daily_category on daily_articles(category);
create unique index if not exists uniq_daily_link on daily_articles(link);
```

### Weekly Articles

<!-- PRD-6.2-1 -->

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
| thumbnail    | text        | 썸네일 URL(선택)               |
| created_at   | timestamptz | 삽입 시각(default now)         |

**권장 인덱스**

<!-- PRD-6.2-2 -->

```sql
create index if not exists idx_weekly_week on weekly_articles(week);
```

> ### DB 마이그레이션 정책
>
> **순서 고정**:
>
> 1. `001_tables` (daily/weekly 테이블)
> 2. `002_indexes` (목록/정렬/중복 unique/보조 인덱스)
> 3. `003_tsv_triggers` (tsvector 컬럼·트리거, `pg_trgm` 포함)
> 4. `004_views` (`unified_articles` 뷰)
> 5. `005_search_rpc` (검색 RPC, _섹션별 상한_ 강제 버전)
>    (선택) 6) `006_policies`(권한/RLS) → MVP는 읽기 전용이면 생략 가능
>    (선택) 7) `007_retention_jobs`(보존 정책 SQL)
>
> **불변 원칙**: 위 번호는 **증분 적용**을 전제로 하며, 상위 번호가 하위 번호를 참조하지 않도록 설계한다.

---

<!-- PRD-7 -->

## 7. 카테고리 분류 규칙

### 소스별 기본값

<!-- PRD-7.1-1 -->

- 한국경제 IT → `IT/과학`

<!-- PRD-7.1-1a -->

- DataNet → `IT/과학`

<!-- PRD-7.1-2 -->

- ZDNet Korea → `IT/기술`

<!-- PRD-7.1-3 -->

- ScienceDaily → `과학`

<!-- PRD-7.1-4 -->

- scienceON → `과학기술`

### 제목 키워드 덮어쓰기

<!-- PRD-7.2-1 -->

- `AI|인공지능|GPT|LLM|딥러닝` → `AI`

<!-- PRD-7.2-2 -->

- `보안|해킹|유출|취약|랜섬` → `보안`

<!-- PRD-7.2-3 -->

- `반도체|칩|파운드리` → `반도체`

<!-- PRD-7.2-4 -->

- `로봇|로보틱스` → `로봇`

<!-- PRD-7.2-5 -->

- `생명|제약|백신|유전체|미생물` → `생명과학`

> <!-- PRD-7-3 --> 로직: **기본값 지정** → **제목 키워드가 있으면 덮어쓰기**.

---

<!-- PRD-8 -->

## 8. 검색 (Search)

<!-- PRD-8-1 -->

- **엔진**: PostgreSQL FTS (`tsvector` + `websearch_to_tsquery`)

<!-- PRD-8-2 -->

- **보완**: `pg_trgm` 인덱스로 국문 부분 일치/유사도

<!-- PRD-8-3 -->

- **범위**: Daily = 최근 14일 / Weekly = 전체

<!-- PRD-8-4 -->

- **정렬**: **관련도(ts_rank) → 최신(sort_time)**

<!-- PRD-8-5 -->

- **표시**: Daily 섹션, Weekly 섹션으로 분리

<!-- PRD-8-6 -->

- **개수 제한(기본)**: 섹션별 최대 50건

FTS 컬럼/인덱스/트리거(요약)

<!-- PRD-8-FTS-1 -->

```sql
-- Daily
alter table daily_articles add column if not exists tsv tsvector;
update daily_articles
set tsv = to_tsvector('simple', coalesce(title,'')||' '||coalesce(summary,'')||' '||coalesce(category,''));
create index if not exists idx_daily_tsv on daily_articles using gin(tsv);
create or replace function trg_daily_tsv_fn() returns trigger as $$
begin
  new.tsv := to_tsvector('simple', coalesce(new.title,'')||' '||coalesce(new.summary,'')||' '||coalesce(new.category,''));
  return new;
end $$ language plpgsql;
drop trigger if exists trg_daily_tsv on daily_articles;
create trigger trg_daily_tsv before insert or update on daily_articles
for each row execute function trg_daily_tsv_fn();

-- Weekly
alter table weekly_articles add column if not exists tsv tsvector;
update weekly_articles
set tsv = to_tsvector('simple', coalesce(title,'')||' '||coalesce(summary,'')||' '||coalesce(category,'')||' '||coalesce(period_label,''));
create index if not exists idx_weekly_tsv on weekly_articles using gin(tsv);
create or replace function trg_weekly_tsv_fn() returns trigger as $$
begin
  new.tsv := to_tsvector('simple', coalesce(new.title,'')||' '||coalesce(new.summary,'')||' '||coalesce(new.category,'')||' '||coalesce(new.period_label,''));
  return new;
end $$ language plpgsql;
drop trigger if exists trg_weekly_tsv on weekly_articles;
create trigger trg_weekly_tsv before insert or update on weekly_articles
for each row execute function trg_weekly_tsv_fn();

-- 국문 보완
create extension if not exists pg_trgm;
create index if not exists idx_daily_title_trgm   on daily_articles using gin (title gin_trgm_ops);
create index if not exists idx_daily_summary_trgm on daily_articles using gin (summary gin_trgm_ops);
create index if not exists idx_weekly_title_trgm   on weekly_articles using gin (title gin_trgm_ops);
create index if not exists idx_weekly_summary_trgm on weekly_articles using gin (summary gin_trgm_ops);
```

---

<!-- PRD-9 -->

## 9. UI/화면 설계

### 상단/공통

<!-- PRD-9.1-1 -->

- 로고/서비스명(좌), 탭(중): **Daily IT/Science / Weekly SciTech**, 검색창, Sign In/Up(우)

<!-- PRD-9.1-2 -->

- 반응형: 데스크탑(사이드바+2\~3열 카드) / 모바일(사이드바 접힘+1열)

### Daily 탭

<!-- PRD-9.2-1 -->

- **사이드바**: 최근 14일 날짜(오늘 `New`)

<!-- PRD-9.2-2 -->

- **기사 영역**: 카드 **10개** 기본 → **Load More**(10개씩 추가)
  - 카드: 제목(원문 링크), 요약, 출처, 발행일, 카테고리, (썸네일)
  - **추후 데이터가 많이 쌓이면** 날짜/주차 목록도 `더보기` 버튼으로 추가 분량을 로드하는 방식(접힘/무한 스크롤) 검토

### Weekly 탭

<!-- PRD-9.3-1 -->

- **사이드바**: 최근 8주 주차(최신 `New`)

<!-- PRD-9.3-2 -->

- **기사 영역**: 카드 10개 기본 → Load More(동일 규칙)

### 검색 결과

<!-- PRD-9.4-1 -->

- **Daily Results (14일)** / **Weekly Results** 섹션 분리

<!-- PRD-9.4-2 -->

- 각 섹션 10개 기본 → Load More

### Load More UX (확정)

<!-- PRD-9.5-1 -->

- 버튼 유지, 클릭 시 **disabled + “Loading…” + 스피너**

<!-- PRD-9.5-2 -->

- 완료 후 정상 복귀, 10개 미만 응답이면 버튼 대신 “No more results”

**접근성**

<!-- PRD-9.6-1 -->

- 탭: WAI-ARIA(Arrow/Home/End)

<!-- PRD-9.6-2 -->

- 버튼: `aria-busy` / `aria-live="polite"`

<!-- PRD-9.6-3 -->

- 로딩 후 추가된 첫 카드에 포커스 이동(키보드 사용자 배려)

---

<!-- PRD-10 -->

## 10. 데이터 수집 파이프라인

### 1) 소스

**Daily (RSS)**

<!-- PRD-10.1-1 -->

- 한국경제 IT: `https://www.hankyung.com/feed/it`

<!-- PRD-10.1-1a -->

- DataNet: `https://www.datanet.co.kr/rss/allArticle.xml`

<!-- PRD-10.1-2 -->

- ZDNet Korea: `https://feeds.feedburner.com/zdkorea`

<!-- PRD-10.1-3 -->

- ScienceDaily: `https://www.sciencedaily.com/rss/top/science.xml`
  ※ 초기 UI 개발은 “한국경제 단일 소스”에서 시작 → 현재 DataNet까지 자동 수집, 이후 ZDNet/ScienceDaily 확장 예정

**Weekly (스크래핑)**

<!-- PRD-10.1-4 -->

- scienceON: `https://scienceon.kisti.re.kr/trendPromo/PORTrendPromoList.do`

### 2) 수집 방식

- **Daily**: `rss-parser` → 정규화 → Supabase `daily_articles` UPSERT (한국경제 IT + DataNet 자동화, ZDNet/ScienceDaily 확장 예정)

<!-- PRD-10.2-1 -->

- `date`: **KST 버킷**(YYYY-MM-DD)

<!-- PRD-10.2-2 -->

- `published_at`: ISO(UTC)

<!-- PRD-10.2-3 -->

- `id`: `SHA1(link)` (fallback 존재)

<!-- PRD-10.2-4 -->

- `summary`: 본문/스니펫에서 2\~3문장(≈180자)(추후 개선 ollama LLM 모델 이용하여 요약)

<!-- PRD-10.2-5 -->

- `category`: 소스 기본값 → 제목 키워드 덮어쓰기

**Weekly**: `axios + cheerio` → 추출 → `weekly_articles` UPSERT (원문 출처·썸네일 유지)

- `services/ingest/run_ingest.py` 스크립트가 Daily(한국경제 IT + DataNet), Weekly(scienceON) 결과를 Supabase REST로 upsert
- GitHub Actions 워크플로(`ingest-daily.yml`, `ingest-weekly.yml`)에서 `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` secret을 환경 변수로 주입해 자동 실행

<!-- PRD-10.2-6 -->

- `week`: `YYYY-MM-N`, `period_label`: 표시용

<!-- PRD-10.2-7 -->

- `id`: `SHA1(source+week+title+link)`

### 3) 스케줄링

<!-- PRD-10.3-1 -->

- Daily: 매일 **06:00 KST**

<!-- PRD-10.3-2 -->

- Weekly: 매주 **월 08:00 KST**

<!-- PRD-10.3-3 -->

- 실행: 로컬 `npm run fetch:*` / 운영 GitHub Actions or Supabase Scheduler

> - **런타임**: GitHub Actions(UTC)
> - **시간 매핑**:
>   - Daily 06:00 **KST** = **전날 21:00 UTC**
>   - Weekly 월 08:00 **KST** = **일 23:00 UTC**
> - **환경 변수**: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `TZ=Asia/Seoul` (레포 secrets)
> - **실행 단위**: `fetch:daily`, `fetch:weekly` **별도 스텝**으로 분리

### 4) 보존 정책

<!-- PRD-10.4-1 -->

- **MVP**: 무제한 저장

<!-- PRD-10.4-2 -->

- (옵션) Daily 30일 / Weekly 26주 (SQL은 PRD-17 참고)

### 5) 데이터 품질

<!-- PRD-10.5-1 -->

- 중복 제거: `id` 및 `link` unique

<!-- PRD-10.5-2 -->

- 타임존: `date`는 KST 버킷, `published_at`은 UTC

<!-- PRD-10.5-3 -->

- 썸네일 null-safe, 요약 길이 제한, 카테고리 규칙 준수

### 6) 확장성(어댑터)

<!-- PRD-10.6-1 -->

- `SourceAdapter.fetch(): Promise<Article[]>` 인터페이스

<!-- PRD-10.6-2 -->

- 소스 추가 시 어댑터 파일 1개만 추가

> ### 요약 정책(MVP)
>
> - **방식**: 규칙 기반 **추출 요약**(비-LLM)
> - **입력 우선순위**: `content:encoded` → `description` → 스니펫 → 제목
> - **가공 규칙**: HTML 제거 → 문장 단위 분할 → **2~3문장, 최대 180자**
> - **길이 초과**: 단어 경계 기준으로 자르고 말줄임표 `…`
> - **부족/결측**: 요약 불가 시 `summary = null` 저장, UI에 **“요약 없음” 배지**
> - **품질 확장(후순위)**: TextRank/LLM은 *실패 시 폴백*으로만 고려

---

<!-- PRD-11 -->

## 11. 후순위(차후 확장)

<!-- PRD-11-1 -->

- Supabase Auth(로그인) + 북마크/즐겨찾기

<!-- PRD-11-2 -->

- 개인화 추천(사용자 키워드/카테고리)

<!-- PRD-11-3 -->

- 요약 품질 개선(LLM API)

<!-- PRD-11-4 -->

- 다국어/해외 소스 확대

---

<!-- PRD-12 -->

## 12. 수용 기준 (Acceptance Criteria)

<!-- PRD-12-1 -->

- Daily 사이드바는 최근 14개의 **서로 다른** `date`를 내림차순 노출한다.

<!-- PRD-12-2 -->

- 날짜 선택 시 기사 **10개**가 최신순으로 표시된다. `Load More` 클릭 시 10개 추가, 10개 미만이면 “No more results”.

<!-- PRD-12-3 -->

- Weekly도 동일 규칙(주차 목록/10개 페이지네이션)으로 동작한다.

<!-- PRD-12-4 -->

- 검색은 Daily(최근 14일)+Weekly(전체)를 동시에 수행하고, 결과를 **관련도 → 최신순**으로 정렬해 섹션 분리 표시한다.

<!-- PRD-12-5 -->

- 카드에는 **제목·요약·출처·일시·카테고리**가 표시되고, 제목 클릭은 새 탭으로 원문을 연다.

---

<!-- PRD-13 -->

## 13. 비기능 요구사항 (NFR)

<!-- PRD-13-1 -->

- 성능: 목록 쿼리 **p95 < 500ms**, 초기 카드 렌더 **FCP < 2.5s**(데스크탑)

<!-- PRD-13-2 -->

- 접근성: 탭/버튼의 ARIA 패턴 준수

<!-- PRD-13-3 -->

- 안정성: 소스 일부 실패해도 나머지는 서비스 지속(부분 실패 토스트)

<!-- PRD-13-4 -->

- SEO/공유: 기본 `<title>`/OG 메타(SSR 미도입 가정)

---

<!-- PRD-14 -->

## 14. 에러·빈 상태 UI

<!-- PRD-14-1 -->

- 빈 결과: “No results found”

<!-- PRD-14-2 -->

- 네트워크 오류: “Network error. Retry”

<!-- PRD-14-3 -->

- 썸네일 없음: 이미지 영역 숨기고 본문 영역 확장

<!-- PRD-14-4 -->

- 수집 실패: “일시적으로 로딩에 실패했습니다. 다시 시도해주세요.”

---

<!-- PRD-15 -->

## 15. 배포·환경 변수 & 스크립트

<!-- PRD-15-1 -->

```
client/.env.local
  NEXT_PUBLIC_SUPABASE_URL=
  NEXT_PUBLIC_SUPABASE_ANON_KEY=

scripts/.env
  SUPABASE_URL=
  SUPABASE_SERVICE_KEY=
  TZ=Asia/Seoul
```

<!-- PRD-15-2 -->

```json
{
  "scripts": {
    "fetch:daily": "node scripts/fetchDaily.js",
    "fetch:weekly": "node scripts/fetchWeekly.js",
    "cron": "node scripts/cron.js"
  }
}
```

---

<!-- PRD-16 -->

## 16. 검색 SQL 부록 (뷰 + RPC + 정렬)

**통합 뷰**

<!-- PRD-16-1 -->

```sql
create or replace view unified_articles as
select
  'daily'::text as kind,
  date as date_key,
  null::text as week_key,
  published_at as sort_time,
  id, source, title, summary, link, category, tsv
from daily_articles
union all
select
  'weekly'::text as kind,
  null::date as date_key,
  week as week_key,
  coalesce(created_at, now()) as sort_time,
  id, source, title, summary, link, category, tsv
from weekly_articles;
```

**검색 RPC (기본: Daily=14일, 섹션별 최대 50, 정렬=관련도→최신)**

<!-- PRD-16-2 -->

> - **반환 제약**: `search_unified(q, …)`는 결과를 **kind(Daily/Weekly)별**로 `rank desc, sort_time desc` 정렬 후, **각 섹션 최대 `max_results`(기본 50)** 까지만 반환한다.
> - 구현 권장: 윈도우 함수 `row_number() over(partition by kind …)`로 상한 적용.

```sql
create or replace function search_unified(
  q text,
  cat text default null,
  d_since interval default '14 days',
  max_results int default 50
) returns table(
  kind text, date_key date, week_key text, sort_time timestamptz,
  id text, source text, title text, summary text, link text, category text, rank float
) language sql as $$
  with qry as (select websearch_to_tsquery('simple', q) as tsq)
  select ua.kind, ua.date_key, ua.week_key, ua.sort_time,
         ua.id, ua.source, ua.title, ua.summary, ua.link, ua.category,
         ts_rank(ua.tsv, (select tsq from qry)) as rank
  from unified_articles ua
  where ua.tsv @@ (select tsq from qry)
    and (ua.kind <> 'daily' or ua.date_key >= current_date - d_since)
    and (cat is null or ua.category = cat)
  order by rank desc, ua.sort_time desc
  limit max_results
$$;
```

---

<!-- PRD-17 -->

## 17. 보존 정책 SQL (안전 버전)

<!-- PRD-17-1 -->

```sql
-- Daily: 30일 이전 삭제 (옵션)
delete from daily_articles
where date < current_date - interval '30 days';

-- Weekly: 26주 이전 삭제는 created_at 기준 권장 (옵션)
delete from weekly_articles
where created_at < now() - interval '26 weeks';
```

---

<!-- PRD-18 -->

## 18. 로깅/분석(선택)

<!-- PRD-18-1 -->

- 이벤트: `select_date`, `select_week`, `search_submit`, `load_more`, `open_link`

<!-- PRD-18-2 -->

- 속성: 검색어, 카테고리, 날짜/주차, 페이지, 결과 수

<!-- PRD-18-3 -->

- 활용: 페이지 사이즈/정렬/사이드바 UX 튜닝 근거 확보

---

<!-- PRD-19 -->

## 19. 리스크 & 대응

<!-- PRD-19-1 -->

- RSS/DOM 구조 변경 → 어댑터·셀렉터 모듈화, 실패 시 소스별 격리 로그

<!-- PRD-19-2 -->

- 과도한 호출/비용 → 크론 수집 고정, 프론트 쿼리 `limit/range` 강제

<!-- PRD-19-3 -->

- 저작권/이용약관 → 원문 링크·출처 명시, 각 사이트 `robots.txt` 준수
- 이미지/텍스트 재사용 이슈 → MVP 단계에서는 원문 썸네일 제거 또는 대체 이미지 사용, 상업화 시 언론사 API/라이선스 체결 또는 AI 생성 이미지·자체 제작 비주얼 도입 검토

<!-- PRD-19-4 -->

- GitHub Actions은 schedule 실행을 best-effort로 처리해서 최대 30분 지연될 수 있다.

---

<!-- PRD-20 -->

## 20. 2주 실행 계획

<!-- PRD-20-1 -->

- **W1**
  - 프로젝트 킥오프 & 기본 세팅
    (레포 초기화, 브랜치 전략/린터/포매터, 환경 변수 스펙 정리)
  - **UI 뼈대 구현 (Mock 데이터 기반)**
    - 레이아웃: 헤더, 탭, 사이드바, 카드 그리드
    - Daily/Weekly 탭 화면, 검색 결과 화면, 로딩/빈 상태/에러 메시지
    - 접근성 패턴(ARIA, 포커스 이동) 적용

  - DB 마이그레이션 정책 확정 (001~005 순서 문서화, 실행은 W2에서 진행)

<!-- PRD-20-2 -->

- **W2**
  - **DB 마이그레이션 실행** (테이블, 인덱스, 트리거, 뷰, RPC)
  - 데이터 수집 파이프라인 설계 & 샘플 적재
    - Daily: 한국경제 + DataNet RSS → Supabase 적재 (요약=규칙 기반 추출, SHA1(link) 중복 방지)
    - Weekly: scienceON 스크래핑 목업/인터페이스 검증

  - **UI ↔ DB 연동**
    - Daily/Weekly 탭 실제 데이터 바인딩
    - 검색 RPC 연동 (관련도 → 최신 정렬, 섹션별 상한 보장)

  - 자동화 및 배포 준비
    - GitHub Actions(UTC 변환) 또는 Supabase Scheduler 선택
    - 실행 로그/에러 알림 채널 지정
    - 운영 FAQ는 `docs/phase7_qna.md` 참고 (검색/배치/서버 온디맨드/데이터 보존)

  - QA & 성능 점검, README/운영 가이드 업데이트

---

## 21. Tech Stack

- **Frontend**: Next.js (React 기반, Vercel 배포 가정)
- **Backend API & Batch**: Node.js + Express
  - 구조: **Controller → Service → Repository** (쿼리/SQL 분리)
  - 문서화: **OpenAPI** 스펙(`/docs/openapi.yaml`) + **Swagger UI**
  - 보안/안정성: **helmet, cors, compression, express-rate-limit**
  - 로깅: **pino-http**(요청 ID) / 에러 핸들러
  - **선정 이유**: Express는 생태계가 넓고 학습곡선이 낮아, 빠른 MVP 개발과 포트폴리오 프로젝트에서 백엔드 역량을 드러내기에 적합하다.

- **Database**: PostgreSQL (Supabase 인스턴스)
- **Language**: JavaScript (차후 TypeScript 확장 고려)
- **Scheduler**: GitHub Actions(권장, UTC↔KST 매핑) 또는 Supabase Scheduler (택1)
