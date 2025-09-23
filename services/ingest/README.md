## Python 가상 환경 세팅

### 루트 경로

```WSL
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 스크래핑 테스트

### Daily (한국경제 IT)

```wsl
cd services/ingest
python hankyung_rss_scraper.py --limit 5 > hankyung_sample.jsonl
```

- 출력: JSON Lines (한 줄당 한 기사)
- 주요 필드: `id`, `source`, `title`, `link`, `author`, `published_at`, `date`, `thumbnail`, `summary`, `body`, `category`
- 요약 규칙: 2~3문장, 180자 이내 (결측 시 `"요약 없음"`)
- 본문이 150자 미만인 기사는 자동 제외

### Weekly (scienceON)

```wsl
cd services/ingest
python science_on_scraper.py list 1 10 > scienceon_sample.json
```

- 목록/상세를 순회하며 주간 기사 모음 추출
- 주요 필드: `id`, `week`, `period_label`, `title`, `summary`, `link`, `source`, `category`, `date`, `original_source`
- `week` 형식: `YYYY-MM-N` (예: `2025-09-4`)
- 요약 규칙 동일, 결측 시 `"요약 없음"`
