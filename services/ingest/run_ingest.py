#!/usr/bin/env python3
"""Ingestion orchestrator for Phase 7 automation.

This script runs the existing scraper CLI tools and upserts the results into
Supabase via the PostgREST API. It is designed to be invoked from CI (e.g.,
GitHub Actions) and keeps stdout concise for easy log inspection.
"""

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
    """Raised when scraping or upserting fails."""


def ensure_env() -> None:
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
    """Run external command and return stdout text."""
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
    for idx in range(0, len(iterable), size):
        yield iterable[idx : idx + size]


def upsert(table: str, rows: List[Dict[str, Any]]) -> None:
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
    params = {"on_conflict": "id"}

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
    cmd = [
        sys.executable,
        "services/ingest/hankyung_rss_scraper.py",
        "--limit",
        str(limit),
    ]
    output = run_command(cmd)
    records = parse_json_lines(output)
    payload = [map_daily(rec) for rec in records]
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    upsert("daily_articles", payload)


def ingest_weekly(pages: int, limit: int, dry_run: bool) -> None:
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
    upsert("weekly_articles", payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ingest pipeline and upsert into Supabase")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    daily_parser = subparsers.add_parser("daily", help="Ingest daily RSS articles")
    daily_parser.add_argument("--limit", type=int, default=30, help="RSS items to fetch")
    daily_parser.add_argument("--dry-run", action="store_true", help="Print payload without upserting")

    weekly_parser = subparsers.add_parser("weekly", help="Ingest weekly scienceON summaries")
    weekly_parser.add_argument("--pages", type=int, default=1, help="Number of list pages to crawl")
    weekly_parser.add_argument("--limit", type=int, default=30, help="Total items upper bound")
    weekly_parser.add_argument("--dry-run", action="store_true", help="Print payload without upserting")

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
