# 서버 데이터 흐름 가이드 - AI 정리

이 문서는 `services/api` 백엔드가 어떻게 DB에서 뉴스를 읽어와 Next.js 프런트엔드에 전달하는지, 파일과 코드 조각별로 단계적으로 설명합니다. 초보자도 한 번에 이해할 수 있도록 흐름도를 따라가며 읽어보세요.

---

## 0. 큰 그림 한눈에 보기

1. **환경 변수 정리** → `services/api/src/config.js:28`
2. **DB 연결 풀 구성** → `services/api/src/db/pool.js:7`
3. **Express 앱 공통 설정** → `services/api/src/app.js:46`
4. **API 라우터 묶기** → `services/api/src/routes/index.js:8`
5. **각 기능 라우터 → 컨트롤러 → 서비스 → 리포지토리**
6. **서버 기동** → `services/api/src/server.js:7`
7. **프런트엔드 Fetch** → `apps/web/lib/api.js:5`
8. **React 훅/페이지에서 UI 렌더링** → 예: `apps/web/hooks/useDailyArticles.js:6`, `apps/web/pages/index.js:35`

---

## 1. 공통 기반 살펴보기

| 단계      | 설명                                                               | 관련 파일                                       |
| --------- | ------------------------------------------------------------------ | ----------------------------------------------- |
| 설정 로딩 | `.env`와 시스템 환경 변수를 읽어 숫자/불린 값으로 정리합니다.      | `services/api/src/config.js:28`                 |
| DB 풀     | PostgreSQL 풀을 만들고 `query()`/`getClient()`를 제공합니다.       | `services/api/src/db/pool.js:7`                 |
| 앱 생성   | CORS, Helmet, 압축, 속도 제한, 로깅, OpenAPI 문서 등을 설정합니다. | `services/api/src/app.js:46`                    |
| 에러 처리 | 404와 기타 에러를 JSON 형태로 응답합니다.                          | `services/api/src/middleware/errorHandler.js:5` |
| 서버 실행 | `createApp()`을 호출해 지정된 포트(기본 4000)에서 리스닝합니다.    | `services/api/src/server.js:7`                  |

> 이 공통 단계는 모든 API 요청이 거치는 기본 틀입니다.

---

## 2. 일간 기사 목록 흐름 (`GET /api/articles/daily`)

DB에 저장된 `public.daily_articles` 데이터를 화면 카드로 보여줄 때 흐름은 아래와 같습니다.

1. **DB 테이블** → `daily_articles`에서 날짜·카테고리 조건으로 기사 목록과 총 개수를 가져옵니다.
   - 코드: `services/api/src/repositories/articlesRepository.js:13` (`fetchDailyArticles`)
   - 역할: SQL을 직접 실행해 `items`와 `total` 을 반환합니다.
2. **서비스 계층** → 파라미터 검증(날짜 형식), 페이지네이션 계산, 응답 구조화.
   - 코드: `services/api/src/services/articlesService.js:18` (`getDailyArticles`)
   - 역할: `DATE_REGEX`로 날짜 형식을 확인하고, `parsePagination`으로 페이지·사이즈를 계산합니다.
3. **컨트롤러** → Express 컨트롤러가 서비스 결과를 `{ data: ... }` JSON으로 응답.
   - 코드: `services/api/src/controllers/articlesController.js:12` (`handleDailyArticles`)
4. **라우터** → `/articles/daily` 경로에 컨트롤러를 연결.
   - 코드: `services/api/src/routes/articlesRoutes.js:15`
5. **라우터 집합 → 앱** → `/api` 아래로 라우터를 붙여 최종 URL이 `/api/articles/daily`가 됩니다.
   - 코드: `services/api/src/routes/index.js:8`, `services/api/src/app.js:95`
6. **서버 실행** → `createApp()`을 실행한 서버가 요청을 받습니다.
   - 코드: `services/api/src/server.js:7`
7. **프런트 호출** → 날짜가 선택될 때 `apiGet('/articles/daily', { date, page, size })` 호출.
   - 코드: `apps/web/lib/api.js:5`, `apps/web/hooks/useDailyArticles.js:22`
8. **UI 렌더링** → 받은 `items`를 리스트 카드로 출력.
   - 코드: `apps/web/pages/index.js:35`

정리: **DB `daily_articles` → Repository `fetchDailyArticles` → Service `getDailyArticles` → Controller `handleDailyArticles` → Route `/articles/daily` → 앱 `/api` → 서버 → 프런트 훅 `useDailyArticles` → 화면**

---

## 3. 주간 기사 목록 흐름 (`GET /api/articles/weekly`)

주간 기사 데이터는 비슷한 구조지만 주차(예: `2024-10-2`)를 기준으로 동작합니다.

1. **DB 테이블** → `weekly_articles`에서 주차·카테고리 조건으로 데이터 조회.
   - 코드: `services/api/src/repositories/articlesRepository.js:65` (`fetchWeeklyArticles`)
2. **서비스 계층** → 주차 문자열이 `YYYY-MM-N` 형식인지 확인하고 페이지네이션 처리.
   - 코드: `services/api/src/services/articlesService.js:48` (`getWeeklyArticles`)
3. **컨트롤러** → JSON 응답 반환.
   - 코드: `services/api/src/controllers/articlesController.js:21` (`handleWeeklyArticles`)
4. **라우터** → `/articles/weekly` 경로 매핑.
   - 코드: `services/api/src/routes/articlesRoutes.js:16`
5. **앱/서버** → `/api/articles/weekly`로 노출.
   - 코드: `services/api/src/app.js:95`, `services/api/src/server.js:7`
6. **프런트 호출** → `useWeeklyArticles` 훅이 주차 값으로 API를 호출하고 상태를 관리.
   - 코드: `apps/web/hooks/useWeeklyArticles.js:22`
7. **UI 렌더링** → 홈 페이지 주간 탭에 카드로 표시.
   - 코드: `apps/web/pages/index.js:44`

정리: **DB `weekly_articles` → Repository → Service → Controller → Route `/articles/weekly` → 앱/서버 → 훅 `useWeeklyArticles` → 화면**

---

## 4. 사이드바 최신 날짜·주차 흐름 (`GET /api/articles/sidebar/*`)

### 4-1. 일간 날짜 목록

1. **DB** → `daily_articles`에서 최근 날짜 14개를 중복 없이 조회.
   - 코드: `services/api/src/repositories/articlesRepository.js:107` (`fetchDailyDates`)
2. **서비스** → 단순히 결과를 전달.
   - 코드: `services/api/src/services/articlesService.js:137` (`getDailySidebar`)
3. **컨트롤러** → `{ data: [...] }` 구조로 응답.
   - 코드: `services/api/src/controllers/articlesController.js:39` (`handleDailySidebar`)
4. **라우터** → `/articles/sidebar/daily` 경로.
   - 코드: `services/api/src/routes/articlesRoutes.js:17`
5. **프런트 훅** → 사이드바에서 호출해 날짜·요일 라벨 생성.
   - 코드: `apps/web/hooks/useDailySidebar.js:24`

### 4-2. 주간 주차 목록

1. **DB** → `weekly_articles`에서 최근 주차 8개 추출.
   - 코드: `services/api/src/repositories/articlesRepository.js:118` (`fetchWeeklyWeeks`)
2. **서비스** → 결과 전달.
   - 코드: `services/api/src/services/articlesService.js:141` (`getWeeklySidebar`)
3. **컨트롤러** → JSON 응답.
   - 코드: `services/api/src/controllers/articlesController.js:48` (`handleWeeklySidebar`)
4. **라우터** → `/articles/sidebar/weekly`.
   - 코드: `services/api/src/routes/articlesRoutes.js:18`
5. **프런트 훅** → 주차 라벨 구성.
   - 코드: `apps/web/hooks/useWeeklySidebar.js:24`

---

## 5. 통합 검색 흐름 (`GET /api/search`)

일간·주간 기사에서 동시에 검색 결과를 얻는 요청입니다.

1. **DB 함수** → Supabase에 정의된 `search_unified` SQL 함수 호출.
   - 코드: `services/api/src/repositories/articlesRepository.js:101` (`searchUnified`)
2. **서비스 처리** → 검색어 공백 제거, 요청 개수 제한(`limit`) 적용, 결과를 `daily`/`weekly`로 분리.
   - 코드: `services/api/src/services/articlesService.js:78` (`getSearchResults`)
3. **컨트롤러** → `{ data: { results: { daily, weekly } } }` 구조로 응답.
   - 코드: `services/api/src/controllers/articlesController.js:30` (`handleSearch`)
4. **라우터** → `/search` 경로 매핑.
   - 코드: `services/api/src/routes/articlesRoutes.js:19`
5. **프런트 호출** → 홈 페이지 검색 폼이 `apiGet('/search', { q })` 실행.
   - 코드: `apps/web/pages/index.js:158`
6. **UI 렌더링** → 검색 결과 섹션에서 일간/주간을 분리해 카드 리스트로 표시.

정리: **DB 함수 `search_unified` → Repository → Service → Controller → Route `/search` → 앱/서버 → 홈 페이지 검색 섹션**

---

## 6. 에러와 로깅 처리 흐름

1. **컨트롤러에서 발생한 에러**는 `next(error)`로 넘겨집니다. → 예: `services/api/src/controllers/articlesController.js:16`
2. **공통 에러 미들웨어**가 상태 코드와 메시지를 판단해 JSON 응답을 작성합니다. → `services/api/src/middleware/errorHandler.js:10`
3. **500번대 에러**가 나면 `pino-http`가 서버 로그에 기록합니다. → `services/api/src/app.js:49`
4. **프런트**는 `apiGet`에서 실패 시 에러 메시지를 추출하고 사용자에게 보여줍니다. → `apps/web/lib/api.js:15`

---

## 7. 요청이 실제로 흐르는 순서 요약

아래는 일간 기사 조회를 예시로 한 전체 흐름입니다.

```
브라우저 (Next.js) --요청--> /api/articles/daily
  ↳ apps/web/lib/api.js:5 (apiGet)
  ↳ apps/web/hooks/useDailyArticles.js:22 (API 호출)
Express 서버
  ↳ services/api/src/server.js:7 (app.listen)
  ↳ services/api/src/app.js:46 (미들웨어, /api 라우터)
  ↳ services/api/src/routes/index.js:8 (라우터 묶음)
  ↳ services/api/src/routes/articlesRoutes.js:15 (경로 정의)
  ↳ services/api/src/controllers/articlesController.js:12 (컨트롤러)
  ↳ services/api/src/services/articlesService.js:18 (비즈니스 로직)
  ↳ services/api/src/repositories/articlesRepository.js:13 (SQL 실행)
  ↳ services/api/src/db/pool.js:7 (PostgreSQL 커넥션)
PostgreSQL (Supabase) --응답--> Express --JSON--> 브라우저 --렌더링-->
```

> 다른 엔드포인트들도 Repository → Service → Controller → Route → App → Server → 프런트 훅 순서를 동일하게 따릅니다. DB 쿼리나 비즈니스 규칙만 달라집니다.

---

## 8. 다음에 보면 좋은 코드 포인트

- **페이지네이션 계산 로직**: `services/api/src/utils/pagination.js:1`
- **HTTP 에러 유틸**: `services/api/src/utils/httpErrors.js:1`
- **API 문서 (Swagger)**: `http://localhost:4000/docs`에서 `docs/openapi.yaml` 미리보기 → `services/api/src/app.js:95`
- **환경 변수 예시**: `services/api/.env.example`

이 문서를 따라가며 실제 파일을 열어보면, 서버가 어떤 순서로 동작하고 프런트와 어떤 방식으로 데이터를 주고받는지 자연스럽게 이해할 수 있습니다.
