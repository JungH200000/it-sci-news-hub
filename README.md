# IT/Science News Hub

IT/Science News Hub는 여러 IT·과학 매체에서 수집한 최신 뉴스를 한 곳에 모아 보여주는 풀스택 서비스입니다. 사용자는 키워드 검색과 카테고리 필터를 통해 필요한 정보를 빠르게 찾을 수 있고, 자동화된 파이프라인이 주기적으로 기사 데이터를 수집·정제합니다.

## 주요 기능

- **뉴스 검색 및 탐색**: 프론트엔드(Next.js)가 카드 기반 피드, 키워드 검색, 사이드바 하이라이트를 제공.
- **콘텐츠 API**: Express 기반 API 서버가 일간·주간·분류별 기사 데이터를 Supabase에서 읽어와 제공합니다.
- **데이터 통합**: 일간(`daily_articles`)·주간(`weekly_articles`) 테이블과 통합 뷰(`unified_articles`)를 활용해 일관된 검색 결과를 반환.
- **자동 수집 파이프라인**: Python 스크립트가 네이버 테크, 한경, ScienceON 등 외부 소스에서 기사를 수집하고 정제합니다.

## 아키텍처 개요

![System Architecture](./docs/presentation/diagram/system_architecture.png)

- `apps/web`: Next.js UI. Supabase 인증 키를 사용해 퍼블릭 데이터를 조회합니다.
- `services/api`: Express 서버. 인증 키와 서비스 키를 이용해 데이터 조회 및 전처리를 담당합니다.
- `services/ingest`: Python 크롤러 및 실행 스크립트. 정기적으로 뉴스 데이터를 적재합니다.
- `supabase`: 로컬 개발용 Supabase 설정 및 마이그레이션 리소스를 포함합니다.

## 프로젝트 구조

```text
.
├── apps/web                 # Next.js 웹 애플리케이션
├── services/api             # Express API 서버
├── services/ingest          # Python 기반 뉴스 수집 스크립트
├── docs                     # 아키텍처 다이어그램 및 문서 자료
├── supabase                 # Supabase 초기화·마이그레이션 파일
├── package.json             # 루트 워크스페이스 설정
└── requirement.txt          # 인게스트 스크립트 Python 의존성
```

## 시작하기

### 필수 조건

- Node.js 20 이상 및 npm
- Python 3.11 이상 (가상환경 권장)
- Supabase 프로젝트 또는 로컬 Supabase CLI (선택)

### 의존성 설치

```bash
# 루트에서 Node.js 의존성 설치
npm install

# Python 가상환경 생성 및 활성화 (Linux/macOS 예시)
python3 -m venv .venv
source .venv/bin/activate

# 인게스트 스크립트 의존성 설치
pip install -r requirement.txt
```

## 환경 변수

`apps/web/.env.local` 또는 루트 `.env` 파일에 아래 값을 설정합니다.

### 프론트엔드 (`apps/web`)

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### API 서버 (`services/api`)

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `DATABASE_PASSWORD` (로컬 개발 시 Supabase 비밀번호 사용)
- `TZ` (예: `Asia/Seoul`)

필요 시 `.env.example` 파일을 추가해 공유 가능한 기본 템플릿을 제공할 수 있습니다.

## 실행 방법

```bash
# Next.js 개발 서버 (기본 포트 3000)
npm run dev:web

# Express API 서버 (기본 포트 4000)
npm run dev:api

# 데이터 수집 파이프라인 (가상환경 활성화 후)
python services/ingest/run_ingest.py
```

- 웹과 API 서버를 동시에 실행하여 통합 화면을 확인할 수 있습니다.
- Python 스크립트는 수집 대상별로 모듈화되어 있으며, `run_ingest.py`에서 순차 실행합니다.

## 운영 및 배포 참고

- Supabase 연결 정보는 환경 변수로만 관리하고 저장소에 커밋하지 않습니다.
- GitHub Actions 등 자동화 워크플로를 사용할 경우, Python 스크립트 실행 주기와 API rate limit을 고려하세요.
