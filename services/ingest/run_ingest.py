"""일간/주간 스크레이퍼를 실행해 Supabase에 데이터를 적재하는 자동화 스크립트."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from typing import Iterable, List, Dict, Any

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
DEFAULT_TIMEOUT = 30
CHUNK_SIZE = 200


class IngestError(RuntimeError):
    """스크래핑 또는 Supabase 적재 과정에서 문제가 발생했음을 나타내는 예외."""


def ensure_env() -> None:
    """필수 환경 변수가 모두 설정되어 있는지 확인한다."""
    missing: List[str] = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_SERVICE_KEY:
        missing.append("SUPABASE_SERVICE_KEY")
    if missing:
        raise IngestError(
            "Missing required environment variables: " + ", ".join(missing)
        )


def run_command(cmd: List[str]) -> str:
    """외부 명령을 실행하고 표준 출력 결과를 문자열로 반환한다."""
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "(no stderr)"
        raise IngestError(
            f"Command failed ({exc.returncode}): {' '.join(cmd)}\n{stderr}"
        ) from exc
    return result.stdout


def parse_json_lines(raw: str) -> List[Dict[str, Any]]:
    """스크레이퍼 결과 문자열을 JSON 객체 리스트로 변환한다."""
    stripped = raw.strip()
    if not stripped:
        return []

    # science_on_scraper.py 목록 모드는 JSON 배열을 출력한다.
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise IngestError(f"Failed to parse JSON array: {exc.msg}") from exc
        if not isinstance(data, list):
            raise IngestError("Expected JSON array from scraper output")
        return data

    records: List[Dict[str, Any]] = []
    for idx, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise IngestError(
                f"Failed to parse JSON on line {idx}: {exc.msg}\nLine content: {line[:200]}"
            ) from exc
    return records


def map_daily(record: Dict[str, Any]) -> Dict[str, Any]:
    """일간 기사 레코드를 Supabase 테이블 구조에 맞게 가공한다."""
    return {
        "id": record.get("id"),
        "date": record.get("date"),
        "source": record.get("source"),
        "title": record.get("title"),
        "summary": record.get("summary"),
        "link": record.get("link"),
        "published_at": record.get("published_at"),
        "category": record.get("category"),
        "thumbnail": record.get("thumbnail"),
    }


def map_weekly(record: Dict[str, Any]) -> Dict[str, Any]:
    """주간 기사 레코드를 Supabase 테이블 구조에 맞게 가공한다."""
    return {
        "id": record.get("id"),
        "week": record.get("week"),
        "period_label": record.get("period_label"),
        "source": record.get("source"),
        "title": record.get("title"),
        "summary": record.get("summary"),
        "link": record.get("link"),
        "category": record.get("category"),
        "thumbnail": record.get("thumbnail"),
    }


def chunk(iterable: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    """리스트를 지정한 크기의 묶음으로 잘라 순차적으로 반환한다."""
    for idx in range(0, len(iterable), size):
        yield iterable[idx : idx + size]


def upsert(table: str, rows: List[Dict[str, Any]], conflict_target: str = "id") -> None:
    """Supabase REST API를 사용해 지정한 테이블에 UPSERT 한다."""
    if not rows:
        print(f"No rows to upsert for {table}.")
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }
    params = {"on_conflict": conflict_target}

    total = 0
    for batch in chunk(rows, CHUNK_SIZE):
        response = requests.post(
            url,
            params=params,
            headers=headers,
            data=json.dumps(batch),
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code >= 400:
            raise IngestError(
                textwrap.dedent(
                    f"""
                    Supabase upsert failed ({response.status_code}) for table {table}.
                    Response: {response.text}
                    """
                ).strip()
            )
        total += len(batch)
    print(f"Upserted {total} rows into {table}.")


def ingest_daily(limit: int, dry_run: bool) -> None: # `limit: 기사 몇 개 가져올지, `dry_run`: DB에 넣지 않고 출력만 할지
    """여러 일간 스크레이퍼를 실행해 일간 기사를 적재한다."""

    def run_daily_scraper(script_path: str) -> List[Dict[str, Any]]:
        # `script_path`를 받아서 아래의 코드 실행
        cmd = [
            sys.executable,
            script_path,
            "--limit",
            str(limit),
        ] # ex) python hankyung_rss_scraper.py --limit 5
        # 결과: JSON Lines / 예: {"id": ..., "title": ..., ...}

        output = run_command(cmd) # 실행 결과를 문자열(JSON Lines 문자열)로 받음
        # 예: '{"id": ..., "title": ..., ...}\n'

        records = parse_json_lines(output) # JSON Lines 문자열을 파싱해서 파이썬 리스트로 반환
        # 예: [ {"id": ..., "title": ..., ...}, {"id": ..., "title": ..., ...}, ... ]


        """ 
        각 scraper가 나름대로 출력한 JSON을 Subapse 테이블 구조(daily_articles)에 맞는 공통 스키마로 변환 
        => 필요 없는 필드 제거, 테이블 column에 맞는 key만 남김, 값이 없으면 None 그대로 """
        return [map_daily(rec) for rec in records]

    # 결과를 담을 리스트 초기화
    # payload = 기사를 담을 리스트 (각 기사는 dict 형태)
    payload: List[Dict[str, Any]] = []

    # scraper 파일 순회
    for script in (
        "services/ingest/hankyung_rss_scraper.py",
        "services/ingest/datanet_scraper.py",
    ):
        payload.extend(run_daily_scraper(script))
    # 해당 scraper 파일을 실행해서 JSON Lines를 dict 리스트로 반환 후 리스트(payload)에 붙여넣기(extend)
    
    # 즉, 각 scraper 파일에서 나온 기사들을 하나의 리스트 payload에 모은다.

    # 중복 제거
    # 기사 결과가 하나라도 있으면 실행
    if payload: 
        dedup: Dict[str, Dict[str, Any]] = {}
        # 변수 이름: 타입 힌트 = 값
        # `dudup`는 문자열 키(str)를 가지고, 값은 dict(그 dict는 str 키와 임의의 값(any))로 이로어진 dict이라는 힌트
        extras: List[Dict[str, Any]] = []
        for item in payload:
            identifier = item.get("id")
            # 각 기사를 순회하면서 id를 확인
            if identifier:
                # id가 존재한다면
                dedup[identifier] = item
                # id -> 기사 형태의 dict
                # 같은 id가 있더라도 마지막 기사가 덮어씌움 -> 중복 제거
            else:
                extras.append(item)
                # id가 없으면 extras에 보관
        
        # `dedup.values()`(id가 있는 중복 제거된 기사들) + extras(id가 없는 기사들)를 합쳐 payload를 만듦
        payload = list(dedup.values()) + extras

    # dry_run=True면 DB에 안 넣고, payload를 JSON 문자열로 출력
    # ensure_ascill=False -> 한글도 깨지지 않고 그대로 출력
    if dry_run:   
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    
    # dry_run=False면 DB에 `upsert` 실행
    # 이미 같은 id가 존재하면 업데이트, 없으면 새로 삽입
    upsert("daily_articles", payload)


def ingest_weekly(pages: int, limit: int, dry_run: bool) -> None:
    """scienceON 스크레이퍼를 실행해 주간 기사를 적재한다."""
    cmd = [
        sys.executable,
        "services/ingest/science_on_scraper.py",
        "list",
        str(pages),
        str(limit),
    ]
    output = run_command(cmd)
    records = parse_json_lines(output)
    payload = [map_weekly(rec) for rec in records]
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    upsert("weekly_articles", payload, conflict_target="week,link")

# 파일의 시작점
def main() -> None:
    """커맨드라인 인터페이스: daily/weekly 중 하나를 선택해 ingest 작업을 수행한다."""

    # "이 프로그램이 어떤 옵션을 받는지”를 설명하는 최상위 파서(메뉴판) 를 만듦.
    # description= 은 -h/--help로 도움말을 볼 때 맨 위에 나오는 설명 문구
    parser = argparse.ArgumentParser(description="스크레이퍼를 실행해 Supabase에 적재합니다")

    # git에 git add, git commit 같은 하위 명령을 만들기 위한 서브커맨드 묶음을 만듦
    # `dest="mode"`: 사용자가 고른 하위 명령의 이름을 args.mode 에 넣어주겠다는 뜻. => daily를 고르면 args.mode == "daily".
    # `required=True`: 반드시 하위 명령 하나를 고르게 강제 => python ingest.py 처럼 아무 것도 안 고르면 에러를 내고 사용법을 보여줌
    subparsers = parser.add_subparsers(dest="mode", required=True)

    """
    `add_parser("daily", ...)`: 하위 명령 이름이 daily인 모드를 만듦 => `python ingest.py daily`
    `add_argument`: ‘daily 전용 옵션’을 추가할 때 쓰는 핸들
        `--limit`: 몇 개의 기사를 가져올 지 정하는 옵션
        `--dry-run`: DB에 저장하지 말고 화면에 출력하라는 옵션 """
    daily_parser = subparsers.add_parser("daily", help="일간 RSS 기사 수집")
    daily_parser.add_argument("--limit", type=int, default=30, help="가져올 RSS 항목 수")
    daily_parser.add_argument("--dry-run", action="store_true", help="적재하지 않고 결과만 출력")

    weekly_parser = subparsers.add_parser("weekly", help="주간 scienceON 기사 수집")
    weekly_parser.add_argument("--pages", type=int, default=1, help="크롤링할 목록 페이지 수")
    weekly_parser.add_argument("--limit", type=int, default=30, help="가져올 기사 최대 개수")
    weekly_parser.add_argument("--dry-run", action="store_true", help="적재하지 않고 결과만 출력")

    # 사용자가 터미널에 입력한 옵션을 읽어와서 `args`라는 담음
    args = parser.parse_args()
    # ex: python ingest.py daily --limit 5 --dry-run
    # args.mode = "daily", args.limit = 5, args.dry_run = True.

    try:
        # 환경 변수(DB 연결 정보)가 잘 있는지 확인
        ensure_env()
        if args.mode == "daily":
            # 사용자가 'daily' 모드를 고르면 `ingest_daily` 실행
            ingest_daily(limit=args.limit, dry_run=args.dry_run)
        elif args.mode == "weekly":
            # 사용자가 'weekly' 모드를 고르면 `ingest_weekly` 실행
            ingest_weekly(pages=args.pages, limit=args.limit, dry_run=args.dry_run)
        else:
            raise IngestError(f"Unsupported mode: {args.mode}")
    except IngestError as exc:
        # 실행 중 문제 발생 -> Error 메시지 출력 후 프로그램 멈춤
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

# 이 파일을 직접 실행했을 때(python ingest.py) -> main() 함수부터 실행
if __name__ == "__main__":
    main()
