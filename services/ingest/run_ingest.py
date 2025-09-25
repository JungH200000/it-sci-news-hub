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


def ingest_daily(limit: int, dry_run: bool) -> None:
    """여러 일간 스크레이퍼를 실행해 일간 기사를 적재한다."""

    def run_daily_scraper(script_path: str) -> List[Dict[str, Any]]:
        cmd = [
            sys.executable,
            script_path,
            "--limit",
            str(limit),
        ]
        output = run_command(cmd)
        records = parse_json_lines(output)
        return [map_daily(rec) for rec in records]

    payload: List[Dict[str, Any]] = []
    for script in (
        "services/ingest/hankyung_rss_scraper.py",
        "services/ingest/datanet_scraper.py",
    ):
        payload.extend(run_daily_scraper(script))

    if payload:
        dedup: Dict[str, Dict[str, Any]] = {}
        extras: List[Dict[str, Any]] = []
        for item in payload:
            identifier = item.get("id")
            if identifier:
                dedup[identifier] = item
            else:
                extras.append(item)
        payload = list(dedup.values()) + extras

    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
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


def main() -> None:
    """커맨드라인 인터페이스: daily/weekly 중 하나를 선택해 ingest 작업을 수행한다."""
    parser = argparse.ArgumentParser(description="스크레이퍼를 실행해 Supabase에 적재합니다")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    daily_parser = subparsers.add_parser("daily", help="일간 RSS 기사 수집")
    daily_parser.add_argument("--limit", type=int, default=30, help="가져올 RSS 항목 수")
    daily_parser.add_argument("--dry-run", action="store_true", help="적재하지 않고 결과만 출력")

    weekly_parser = subparsers.add_parser("weekly", help="주간 scienceON 기사 수집")
    weekly_parser.add_argument("--pages", type=int, default=1, help="크롤링할 목록 페이지 수")
    weekly_parser.add_argument("--limit", type=int, default=30, help="가져올 기사 최대 개수")
    weekly_parser.add_argument("--dry-run", action="store_true", help="적재하지 않고 결과만 출력")

    args = parser.parse_args()

    try:
        ensure_env()
        if args.mode == "daily":
            ingest_daily(limit=args.limit, dry_run=args.dry_run)
        elif args.mode == "weekly":
            ingest_weekly(pages=args.pages, limit=args.limit, dry_run=args.dry_run)
        else:
            raise IngestError(f"Unsupported mode: {args.mode}")
    except IngestError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
