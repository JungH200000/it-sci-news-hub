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

### Daily (한국경제 IT, DataNet)

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

#### 자동 실행 (Daily)

```wsl
python services/ingest/run_ingest.py daily --limit 50
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
