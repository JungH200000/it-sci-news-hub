## 📑 PPT 슬라이드 초안 (10~12장 기준)

### 1. 표지

- **제목**: `IT/과학 뉴스 모아보기 & 요약 웹앱 (2주 개인 프로젝트)`
- **핵심 문구**: “여러 매체 IT/과학 뉴스를 한 곳에서 보고, 빠르게 파악하기 위한 MVP”
- **비주얼**: 심플한 배경 + 뉴스/검색 아이콘 + 기간(2주), 개인 프로젝트 표시

---

### 2. 프로젝트 개요 & 문제 정의

- **제목**: `왜 이 프로젝트인가?`

- **내용**:
  - 기존 문제점 (뉴스 분산, 편향, 주제별 큐레이션 부재)
  - 프로젝트 목적 (한 곳에 모아보고, 간단 요약 + 검색)
- **핵심 문구**:
  - 여러 매체 뉴스가 분산되어 파편적
  - 편향 없는 IT/과학 뉴스 플랫폼 부재
  - 최신 동향을 빠르게 파악하기 어려움

- **비주얼**: 간단 인포그래픽 vs 기존 뉴스 사이트 스크린샷 vs 내 서비스 컨셉 다이어그램

---

### 3. 시스템 개요도 (아키텍처)

- **제목**: `전체 구조`

- **내용**: 수집(Ingest) → 저장(DB) → API → UI(웹) 흐름
- **핵심 문구**:
  - 수집(Ingest) → 저장(DB) → API → UI
  - 자동화된 데이터 흐름으로 안정적 제공

- **비주얼**: 블록 다이어그램
  - frontend : next.js기반 반응형 웹 인터페이스)
  - backend : express api 서버 - daily와 weekly로 구분
  - database : supabase postgreSQL
  - automation : github actions
  - 동작:
    - 스크래핑 후 저장: Python/GitHub Actions → Supabase
    - 카드 뉴스
      - Next.js UI (daily or weekly 선택) → Express API (UI에서 선택한 것에 따라 daily or weekly 선택)
      - Supabase (daily_articles or weekly_articles) → Express API → Next.js UI (카드 뉴스)
    - search
      - Next.js UI (search) → Express API (Supabase의 unified_articles 연결)
      - Supabase (unified_articles) → Express API → Next.js UI (Search Results에 카드 뉴스 형태로 출력)

---

### 4. 모듈 개요도

- **제목**: `주요 모듈과 기능`

- **내용**: 주요 모듈과 역할
  - 수집 모듈 (RSS/스크래핑 + GitHub Actions)
  - 저장 모듈 (Supabase/PostgreSQL)
  - 검색 모듈 (FTS + `pg_trgm`)
  - 요약 모듈 (규칙 기반 1~2문장 추출)
  - UI 모듈 (Next.js, 카드뷰, 날짜/주차 탐색)

- **비주얼**: 박스+화살표로 연결

---

### 5. 구현 환경 및 개발 소프트웨어

- **제목**: `개발 환경 & 기술 스택`

- **내용**:
  - 개발환경: WSL Ubuntu + VS Code
  - 언어/프레임워크: Python, Node.js(Express), Next.js
  - DB: Supabase(PostgreSQL)
  - 배치 자동화: GitHub Actions

- **비주얼**: 기술 로고 아이콘 (Node, Python, PostgreSQL, GitHub, Next.js)

---

### 6. DB 테이블 구성

- **제목**: `DB 설계`

- **내용**:
  - 주요 테이블 (`daily_articles`, `weekly_articles`)
  - 통합 뷰(`unified_articles`)
  - 칼럼 예시 (id, source, title, summary, link, published_at, category, thumbnail)

- **비주얼**: 간단한 ERD + 모듈 연계 (수집 → DB → 검색/요약 → UI) vs 간단한 ERD (daily ↔ weekly ↔ unified 뷰)

---

### 7. 가장 중요한 모듈 – 요약 & 검색

- **제목**: `핵심 기능`

- **요약 모듈**: 규칙 기반 (기사 1~2문장 추출)
  - 장점: 빠름/비용 0/대체로 핵심 파악 가능
  - 한계: 의미적 요약 아님

- **검색 모듈**: PostgreSQL FTS + `pg_trgm`
  - 빠른 검색, 부분 일치·오타 대응

- **비주얼**: 예시 쿼리 결과 + 카드뷰에 표시된 모습

---

### 8. UI / 사용자 흐름

- **내용**:
  - Daily/Weekly 탭, 사이드바, 카드뷰, Load More
  - 반응형 지원

- **비주얼**: 실제 웹 화면 캡처 (데스크톱/모바일)

---

### 9. 시연 동영상

- **내용**: 데이터 수집 → 검색 → 요약 표시 → 주간 뉴스 확인
- **비주얼**: 1분 이내 영상 or GIF

---

### 10. 해결한 문제 vs 미해결 과제

- **제목**: `성과와 한계`

- **해결**:
  - 다중 소스 자동 수집
  - 날짜/주차별 정리
  - 기본 요약 제공
  - 검색 기능 구현
  - 자동화

- **미해결**:
  - 주제별 분류/클러스터링
  - 고도화된 요약(LLM)

- **멘트**: “MVP 수준에서는 핵심 흐름을 검증했습니다.”

---

### 11. 향후 계획

- **제목**: `확장 가능성`
- **핵심 문구**:
  - 단기: 소스 확대, 중복/유사 기사 병합
  - 중기: LLM 기반 요약, 주제별 클러스터링(HDBSCAN+pgvector)
  - 장기: 편향 보정, 개인화 기능

- **비주얼**: 로드맵 타임라인 (단기 → 중기 → 장기)

---

### 12. 회고 (옵션)

- **내용**:
  - 배운 점: 자동화 파이프라인 경험, PostgreSQL 고급 검색 활용
  - 아쉬운 점: 시간 제한 → MVP 범위 설정의 중요성(요약/분류 미구현)
  - 다음 목표: 확장성과 실용성 강화

- **비주얼**: 간단한 3개 불릿 + 아이콘

---

## ✨ 포인트

- **개요도 → 모듈 개요도 → DB 연계** 흐름은 참고 자료의 평가 기준을 충족
- **가장 중요한 모듈**을 따로 강조 → 평가자 눈에 프로젝트 핵심이 잘 보임
- **시연 영상**은 꼭 준비 (네트워크 이슈 대비 스샷도 준비)

## ✨ 핵심 팁

- **초반(개요·문제 정의)**: 비전 강조
- **중반(아키텍처·모듈·DB·UI)**: “이만큼 구현했다” 강조
- **후반(성과·한계·향후 계획)**: “완벽하진 않지만 MVP로 충분히 검증했다” 강조
