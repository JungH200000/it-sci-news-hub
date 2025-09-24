# Phase 7 Q&A

## 1. 검색 기능 구현 방식은?
- PostgreSQL Full Text Search(FTS)를 사용하고, `daily_articles`/`weekly_articles`에 `tsvector` 컬럼과 GIN 인덱스를 둔다.
- 트리거로 `title + summary + category`(Weekly는 `period_label` 포함)를 결합해 검색용 텍스트를 갱신하고, `search_unified(q, cat, d_since, max_results)` 함수가 `websearch_to_tsquery('simple', q)` 기반으로 kind별 결과를 반환한다.
- Express API는 이 RPC를 호출해 Daily/Weekly 섹션을 나누고, 최대 50건 제한·카테고리 필터 등을 그대로 적용해 프론트에 전달한다.

## 2. Phase 7 자동화 계획은?
- GitHub Actions cron으로 Daily/Weekly 스크래퍼를 스케줄링하고, 실행 시 Supabase 환경 변수(Secrets) 주입 → Python 스크립트 실행 → upsert 스크립트로 DB 저장 흐름을 하나의 job에 묶는다.
- 프런트/API 배포는 서버리스/온디맨드 환경(Vercel, Railway 등)을 사용해 필요할 때만 기동하고, Actions 로그+웹훅으로 실패 알림/관측성을 확보한다.

## 3. 서버를 항상 켜둘 수 없을 때의 대응은?
- 스케줄러(GitHub Actions 등)가 크론 시간에 스크래핑+Supabase upsert를 수행해 데이터를 미리 쌓아 둔다.
- 웹/API는 필요할 때만 수동/온디맨드로 띄워도 DB가 최신 상태라 바로 서비스를 제공할 수 있다.
- 실제 배포 시에는 상시 구동 가능한 호스팅으로 전환하되, 개발 중에는 “데이터는 자동 적재, 서버는 필요 시 기동” 구조로 운영한다.

## 4. 기존/신규 데이터 보존 방식은?
- Daily/Weekly 테이블은 링크 기반 해시를 PK로 삼아 UPSERT 한다. 기존 A 데이터는 그대로 남고, 새로 수집된 B·C는 추가되거나 갱신된다.
- 별도 보존 정책(예: Daily 30일, Weekly 26주)을 돌리지 않는 한 데이터가 자동 삭제되지는 않는다.
