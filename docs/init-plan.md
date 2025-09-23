# ✅ 초기 실행 계획 (init-plan)

## Tech Stack

- Frontend: **Next.js** (React 기반, Vercel 배포 가정)
- Backend API & Batch: **Node.js + Express**
  - 구조: **Controller → Service → Repository** (쿼리/SQL 분리)
  - 문서화: **OpenAPI** 스펙(`/docs/openapi.yaml`) + **Swagger UI**
  - 보안/안정성: **helmet, cors, compression, express-rate-limit**
  - 로깅: **pino-http**(요청 ID) / 에러 핸들러

- Database: **PostgreSQL (Supabase 인스턴스)**
- Language: **JavaScript** (차후 TypeScript 확장 고려)
- Scheduler: **GitHub Actions**(권장, UTC↔KST 매핑) 또는 **Supabase Scheduler** (택1)

---

## Phase 1. 킥오프 & 공통 세팅

- [O] PRD 범위·MVP 스코프 잠금 _(ref: PRD-5, PRD-20)_ – Daily/Weekly 기본 범위와 스케줄·UI·검색 요구 정리 완료
- [O] `.gitignore`/린터/포매터 명시 _(ref: PRD-13)_ – 루트에 `.gitignore`, `.eslintrc.json`, `.prettierrc` 추가
- [O] **폴더 스캐폴딩**: `/apps/web`, `/services/api`, `/services/ingest`, `/supabase/migrations`, `/docs`, `/infra/ci`
- [O] 환경 변수 스펙 문서화: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `TZ=Asia/Seoul` _(ref: PRD-15-1)_ – `docs/env.md` 작성, 루트 `.env` 사용
- [O] **DB 마이그레이션 정책만 문서화(실행은 Phase 3)**: 001*tables → 002_indexes → 003_tsv_triggers → 004_views → 005_search_rpc *(ref: PRD-6, PRD-16)\* – `docs/db-migrations.md` 작성
- DoD: Next.js dev 서버, **Express `/healthz`** 로컬 기동 확인 – `apps/web`(Next.js) 및 `services/api`(Express) 부트스트랩 완료. `npm run dev:web`, `npm run dev:api`로 기동 검증함.

## Phase 2. 프론트엔드 **UI 뼈대** (Mock 데이터)

- [O] 레이아웃: 헤더/탭(“Daily IT/Science / Weekly SciTech”)/사이드바/카드 그리드 _(ref: PRD-9.1-1, PRD-9.1-2)_ – `apps/web/pages/index.js`, `styles/globals.css`에 블루/화이트 톤 레이아웃 구성
- [O] Daily 탭: 최근 14일(더미), 카드 10개 + **Load More** UX, 접근성 _(ref: PRD-9.2-1, PRD-9.2-2, PRD-9.5-1\~2, PRD-9.6-1\~3)_ – 더미 데이터와 탭 ARIA 패턴, Load More 포커스 이동 처리
- [O] Weekly 탭: 최근 8주(더미), 카드 10개 + Load More _(ref: PRD-9.3-1, PRD-9.3-2)_ – 동일 UX로 주간 패널/사이드바 구현
- [O] 검색 결과: **Daily(14일) / Weekly(전체)** 섹션 분리, 각 10개 기본 + Load More _(ref: PRD-9.4-1, PRD-9.4-2)_ – 검색 폼과 mock 검색 로직, 섹션별 Load More/상태 메시지 적용
- [O] 카드: 제목(새 탭), 요약, 출처, 일시, 카테고리, 썸네일 null-safe _(ref: PRD-12-5, PRD-14-3)_ – 카드 메타/썸네일 조건 렌더링으로 요구 충족
- DoD: 더미 JSON으로 라우팅/상태/접근성 포함 **E2E 화면 시연 가능**

## Phase 3. DB & 검색 기반 준비 (이때 마이그레이션 실행)

- [O] **마이그레이션 실행**: 001*tables, 002_indexes, 003_tsv_triggers, 004_views, 005_search_rpc *(ref: PRD-6, PRD-8, PRD-16)\* – `supabase/migrations/001~005.sql` 작성 및 `supabase/migrations/README.md` 실행 가이드 추가
- [O] 검색 RPC 요구사항 확정: **kind별 섹션 상한(기본 50)** 보장 _(ref: PRD-8-6, PRD-16-2)_ – `005_search_rpc.sql`에서 `row_number()` 파티션으로 Daily/Weekly 각 50건 제한
- [O] 사이드바 쿼리 성능 검증: `distinct date limit 14`, `distinct week limit 8` _(ref: PRD-12-1, PRD-12-3)_ – `docs/db-migrations.md`에 예시 SQL과 실행 체크리스트 문서화
- [O] (옵션) 유니크 보강: `weekly(week, link)` unique _(ref: PRD-6.2-2)_ – `002_indexes.sql`에 `uniq_weekly_week_link` 포함
- DoD: 빈 DB에 idempotent 적용, 대표 쿼리 p95 < 500ms 근접 – `docs/db-migrations.md` 성능 확인 절차 추가, GIN/tsvector 구성 완료

## Phase 4. **Express 백엔드(API) 설계/구현**

- [O] **OpenAPI 스펙** `/docs/openapi.yaml` 초안 작성 + **Swagger UI** 연결 – 3개 엔드포인트 및 사이드바 보조 API 정의, 표준 에러 스키마 포함
- [O] 엔드포인트
  - `GET /articles/daily?date=YYYY-MM-DD&category=&page=&size=` _(ref: PRD-12-1\~2)_ – 컨트롤러/서비스/레포지토리 분리(`services/api/src/...`)
  - `GET /articles/weekly?week=YYYY-MM-N&category=&page=&size=` _(ref: PRD-12-3)_ – 주차 필터/페이지네이션 적용
  - `GET /search?q=&cat=&limit=` → **관련도→최신**, **섹션별 상한** 보장 _(ref: PRD-8-4\~6, PRD-16-2)_ – `search_unified` 호출로 kind별 50건 제한 유지

- [O] 미들웨어/운영: helmet, cors, compression, **express-rate-limit**, **pino-http**, 에러 핸들러, ETag/Cache-Control(검색은 no-store 권장) – `services/api/src/app.js`에서 공통 미들웨어 구성
- [O] 레이어 분리: Controller(HTTP) ↔ Service(정렬·비즈 규칙) ↔ Repository(SQL/RPC 호출) – 각각 `controllers/`, `services/`, `repositories/` 디렉터리로 구조화
- [O] 헬스체크 `/healthz`와 상태 코드 표준화 – `createApp()` 내 `/healthz` 유지, 에러 미들웨어 JSON 응답 일원화
- DoD: 샘플 데이터로 3개 엔드포인트 정상 응답 + Swagger UI 확인 – 로컬 DB 연결 시 `npm --workspace services/api run dev` 후 `/api/...` 호출 및 `/docs/openapi.yaml` 기반 Swagger UI 연동 예정

## Phase 5. **데이터 수집 배치(ingest) 설계/구현**

- “**수집 서비스는 Python으로 구현(services/ingest-py)**, Supabase REST로 upsert. 스케줄러는 GitHub Actions(UTC↔KST 매핑).”
- [O] 요약 정책: **규칙 기반 추출 요약(2\~3문장 / ≤180자)**, 결측 시 “요약 없음” _(ref: PRD-4-2, PRD-10.2-4, PRD-14-1)_ – `hankyung_rss_scraper.py`, `science_on_scraper.py`에서 요약 함수 도입 및 폴백 처리
- [O] Daily(RSS) 어댑터: 한국경제 IT → KST 버킷/UTC 저장, **sha1(link)** 중복 방지, 썸네일 null-safe _(ref: PRD-10.1-1, PRD-10.2-1\~5, PRD-10.5)_ – SHA1 ID, 150자 미만 본문 제외, `thumbnail`/`summary` 보강
- [O] Weekly(scienceON) 어댑터: `week=YYYY-MM-N` 규칙 고정, `period_label` 유지 _(ref: PRD-10.1-4, PRD-10.2-6\~7)_ – 목록/상세 통합, `derive_week_key`로 주차 키 생성, `period_label` 함께 출력
- [O] 실패 격리/재시도/백오프, 소스별 구조화 로그, 알림 경로 _(ref: PRD-19-1, PRD-13-3)_ – requests 세션에 Retry 구성, HTTP 실패 시 stderr 경고 로깅
- DoD: 수동 실행으로 Daily/Weekly 각각 3\~5건 **upsert 성공** – `hankyung_rss_scraper.py --limit 5`, `science_on_scraper.py list 1 5` 실행 결과 확인(샘플 JSON 기록)

## Phase 6. **UI ↔ API/DB 연동**

- [ ] Daily/Weekly 탭: 실제 API 바인딩, 최신순 10개 + Load More _(ref: PRD-12-1\~3)_
- [ ] 검색: RPC 연동, 결과 **섹션 분리 & 섹션별 상한** 보장 _(ref: PRD-8-4\~6)_
- [ ] 빈/에러/로딩 상태 → 실 호출 흐름 연결 _(ref: PRD-14-1, PRD-14-2, PRD-14-4)_
- DoD: Acceptance Criteria 전부 충족(§12), p95 < 500ms 목표 근접

## Phase 7. 자동화/배포/관측성

- [ ] 스케줄러 **옵션 확정**
  - **GitHub Actions(권장)**: KST 06:00/월 08:00 → **UTC 21:00/23:00** 매핑 _(ref: PRD-10.3)_
  - (대안) Supabase Scheduler

- [ ] CI: lint/test/build, API smoke test, ingest dry-run
- [ ] 배포: Web(Vercel), **API/ingest 별도 호스팅**(Railway/Render/Fly/Heroku/서버)
- [ ] 관측성: 실행 로그 보관, 실패 알림(웹훅/메일), 간단 대시보드(수집 건수/실패율)
- DoD: 스케줄 1회 수동 트리거 성공, 실데이터 카드 렌더 확인

---

## 🧪 백엔드 어필 포인트 (Express)

- [ ] **OpenAPI + Swagger UI** 스크린샷/링크를 README 상단에 배치
- [ ] **인덱스 & 쿼리 설계 이유** 문서(`/docs/db-design.md`): 정렬/검색 인덱스 선정 근거
- [ ] **성능 수치**(예: “검색 p95 320ms @ 50RPS”) `/docs/perf.md`
- [ ] **재시도/백오프/타임아웃** 정책 및 scienceON DOM 변경 대응 플로우
- [ ] **요청 ID 로깅**으로 ingest ↔ api 상관관계 추적(pino-http)

---

## 🔗 PRD 참조(ID)

- 데이터 구조/검색: **PRD-6, PRD-8, PRD-16**
- 수집/스케줄/품질: **PRD-10, PRD-19**
- UI/UX/AC: **PRD-9, PRD-12, PRD-14**
- NFR/배포: **PRD-13, PRD-15**
- 실행 계획: **PRD-20**

---
