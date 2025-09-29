## Python 가상 환경 세팅

### 루트 경로

```WSL
sudo apt update
sudo apt install python3-venv python3-pip -y
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

## 스크래핑 테스트

### 과정

터미널 실행

➡️ main()
➡️ 옵션 읽기(--limit)
➡️ RSS에서 기사 링크 목록 뽑기
➡️ 각 링크로 실제 기사 페이지 들어가서

- 대표 이미지 찾기
- 본문 텍스트 긁기
- (필요시 메타 설명 보조로 사용)
- 요약 만들기(2~3문장, ≤180자)
- 카테고리 라벨 붙이기(제목 키워드)
- 시간 표준화(UTC) + KST 날짜 버킷
- 블랙리스트 필터로 잡음 제거

➡️ 최종 결과를 “한 기사 = 한 줄 JSON” 으로 출력

### Daily (한국경제 IT, DataNet)

```wsl
cd services/ingest
python naver_tech_scraper.py --limit 5 > naver_tech_sample.json
```

```wsl
cd services/ingest
python hankyung_rss_scraper.py --limit 5 > hankyung_rss_sample.json
```

```wsl
cd services/ingest
python datanet_scraper.py --limit 5 > datanet_sample.json
```

- 출력: JSON Lines (한 줄당 한 기사)
- 주요 필드: `id`, `source`, `title`, `link`, `author`, `published_at`, `date`, `thumbnail`, `summary`, `body`, `category`
- 요약 규칙: 2~3문장, 180자 이내 (결측 시 `"요약 없음"`)
- 본문이 150자 미만인 기사는 자동 제외
- 네이버 기사에는 `source`(원본 매체)와 `distributor`(제휴 포털) 필드가 함께 포함됩니다.

#### 자동 실행 (Daily)

```wsl
python services/ingest/run_ingest.py daily --limit 30
```

- 한국경제 IT + DataNet 스크레이퍼를 순차 실행해 통합 결과를 `daily_articles`에 upsert 합니다. `--dry-run` 옵션으로 적재 없이 결과만 확인할 수 있습니다.

### Weekly (scienceON)

```wsl
cd services/ingest
python science_on_scraper.py list 1 10 > scienceon_sample.json
```

- 목록/상세를 순회하며 주간 기사 모음 추출
- 주요 필드: `id`, `week`, `period_label`, `title`, `summary`, `link`, `source`, `category`, `date`, `original_source`
- `week` 형식: `YYYY-MM-N` (예: `2025-09-4`)
- 요약 규칙 동일, 결측 시 `"요약 없음"`

#### 자동 실행 (weekly)

```wsl
python services/ingest/run_ingest.py weekly --pages 1 --limit 4
```

- ScienceON 스크레이퍼를 실행해 통합 결과를 `daily_articles`에 upsert 합니다. `--dry-run` 옵션으로 적재 없이 결과만 확인할 수 있습니다.
