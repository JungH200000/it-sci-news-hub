# hankyung_rss_scraper.py
"""한국경제 IT RSS를 수집해 Supabase 적재용 JSON Lines 형태로 가공하는 스크립트."""
# Fields: id, source, title, link, author, published_at(UTC ISO), date(KST), thumbnail, body, category

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter, Retry
import feedparser
from bs4 import BeautifulSoup
# BeautifulSoup은 여러 파서를 지원하지만 여기서는 'lxml'을 사용합니다.

# --- [상수 설정] ---
RSS_URL = "https://www.hankyung.com/feed/it"
SOURCE_NAME = "한국경제 IT"
KST = ZoneInfo("Asia/Seoul")

# --- [HTTP 세션 준비] ---
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))
session.headers.update({
    # 일반 브라우저 UA를 사용해 차단·리디렉션 가능성을 낮춥니다.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})


# --- [카테고리 규칙: 기본값 + 제목 키워드 덮어쓰기] ---
CATEGORY_DEFAULT = "IT/과학"
CATEGORY_RULES = [
    (re.compile(r"(AI|인공지능|GPT|LLM|딥러닝)", re.I), "AI"),
    (re.compile(r"(보안|해킹|유출|취약|랜섬)", re.I), "보안"),
    (re.compile(r"(반도체|칩|파운드리)", re.I), "반도체"),
    (re.compile(r"(로봇|로보틱스)", re.I), "로봇"),
    (re.compile(r"(생명|제약|백신|유전체|미생물|바이오|신약|항암제|안약|줄기세포|장|척수|미트콘드리아|암|간|근육|고혈압|수면|DNA|세포|머리카락|여드름|알츠하이머|항생제|바이러스|박테리아)", re.I), "생명과학"),
    (re.compile(r"(배터리|전지)", re.I), "배터리"),
]

BLACKLIST_KEYWORDS = {
    "부동산", "아파트", "채권", "주식", "환율", "외환", "물가", "금리",
    "취업", "채용", "노동", "고용", "인사", "임금", "연봉",
    "규제", "과징금", "제재", "검찰", "경찰", "사건", "소송", "재판",
    "선거", "정치", "외교", "안보", "헌신", "관세", "영양제", "외래환자",
    "LCK", "가족 친화 경영", "전산시스템", "다이소", "젠지", "박카스", 
    "폭발한", "무서워", "스크래치", "창업자", "붉은사막", "RPG", "서브컬쳐",
    "플로깅", "헌혈", "화백", "티맵", "위약금", "트럼프"
}

def sanitize_title(value: str) -> str:
    """RSS에서 내려온 제목에서 이스케이프 문자와 큰따옴표를 제거한다."""
    if not value:
        return ""
    cleaned = value.replace('\\', '')
    cleaned = cleaned.replace('"', '')
    return cleaned.strip()

def categorize(title: str) -> str:
    """제목을 보고 카테고리를 결정한다(기본값 → 규칙으로 덮어쓰기)."""
    cat = CATEGORY_DEFAULT
    if not title:
        return cat
    for pattern, label in CATEGORY_RULES:
        if pattern.search(title):
            return label
    return cat


def _normalize(text: str | None) -> str:
    """텍스트를 소문자로 변환하고 `None`이면 빈 문자열을 돌려준다."""
    if not text:
        return ""
    return text.lower()

def is_relevant(*texts: str | None) -> bool:
    """텍스트에 블랙리스트 키워드가 포함되어 있지 않을 때만 True를 반환한다."""
    # 블랙리스트 키워드가 포함되면 제외
    for raw in texts:
        normalized = _normalize(raw)
        if not normalized:
            continue
        for keyword in BLACKLIST_KEYWORDS:
            if keyword in normalized:
                return False
    return True


SENTENCE_ENDINGS = ['다.', '다?', '다!', '.', '!', '?', '…']


def ensure_sentence_boundary(text: str, truncated: bool = False) -> str:
    """요약이 문장 중간에서 끊기지 않도록 마지막 완결 문장까지만 남긴다."""
    text = (text or '').strip()
    if not text:
        return text
    end_positions: list[int] = []
    for ending in SENTENCE_ENDINGS:
        idx = text.rfind(ending)
        if idx != -1:
            end_positions.append(idx + len(ending))
    if end_positions:
        return text[:max(end_positions)].strip()
    if truncated:
        return text.rstrip('.') + '…'
    return text


# ---- Utils ----
def sha1_hex(s: str) -> str:
    """문자열을 SHA1 해시로 40자리 헥사 문자열로 변환(고유 ID 생성 용도)."""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def parse_pubdate_to_utc_iso(pubdate: str | None) -> str | None:
    """
    RSS pubDate(예: 'Mon, 22 Sep 2025 12:17:43 +0900')를
    'UTC ISO8601'(예: '2025-09-22T03:17:43+00:00')로 변환.
    """
    if not pubdate:
        return None
    try:
        dt = parsedate_to_datetime(pubdate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.isoformat()
    except Exception:
        return None

def kst_bucket_date_from_utc_iso(utc_iso: str | None) -> str | None:
    """
    UTC ISO 문자열을 KST 날짜(YYYY-MM-DD)로 변환해 '버킷 키'로 사용.
    (사이드바 날짜/일별 목록 쿼리를 위해 PRD에서 분리 보관)
    """
    if not utc_iso:
        return None
    try:
        dt = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
        kst_dt = dt.astimezone(KST)
        return kst_dt.date().isoformat()
    except Exception:
        return None

def text_collapse(s: str) -> str:
    """여러 공백/탭을 한 칸으로 줄이고 양끝 공백 제거(본문 출력 품질 개선)."""
    return re.sub(r"[ \t\r\f\v]+", " ", s).strip()


def clean_text(s: str | None) -> str:
    if not s:
        return ""
    return text_collapse(s)


def html_to_text(html: str | None) -> str:
    """HTML 문자열에서 태그를 제거하고 순수 텍스트만 반환한다."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    return clean_text(soup.get_text(" ", strip=True))


def summarize_text(text: str, max_sentences: int = 3, max_chars: int = 180) -> str | None:
    """간단한 규칙 기반 요약: 앞쪽 문장 2~3개를 취하고 180자 내로 제한."""
    if not text:
        return None

    normalized = text.replace("\n", " ")
    candidates = re.split(r"(?<=[.!?\u3002\uFF01\uFF1F])\s+", normalized)
    sentences = []
    for cand in candidates:
        cleaned = text_collapse(cand)
        if cleaned:
            sentences.append(cleaned)
        if len(sentences) >= max_sentences:
            break

    if not sentences:
        return None
    selected: list[str] = []
    truncated = False
    for sent in sentences:
        candidate = " ".join(selected + [sent]) if selected else sent
        if len(candidate) > max_chars:
            truncated = True
            break
        selected.append(sent)

    if not selected:
        truncated = True
        summary = sentences[0][:max_chars].strip()
    else:
        summary = " ".join(selected).strip()
        if len(summary) > max_chars:
            truncated = True
            summary = summary[:max_chars].strip()

    summary = ensure_sentence_boundary(summary, truncated)
    if not summary:
        fallback = ensure_sentence_boundary(sentences[0][:max_chars].strip(), True)
        return fallback or None
    return summary


# --- [기사 페이지 파싱] ---
def extract_article_details(article_url: str) -> tuple[str | None, str | None, str | None]:
    """
    한국경제 기사 페이지에서 (대표 이미지 URL, 본문 텍스트, 메타 설명)을 추출한다.
    - 대표 이미지: div.article-body > figure.article-figure > div.figure-img > img
    - 본문 텍스트: div.article-body 내부에서 p/li 등을 모아 정리
    - 이미지가 없으면 og:image 메타태그를 폴백으로 사용
    - 예외가 발생하면 (None, None)을 반환한다.
    """
    try:
        r = session.get(article_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[warn] failed to fetch article: {article_url} ({e})", file=sys.stderr)
        return (None, None)

    # BeautifulSoup with lxml parser for speed/robustness
    soup = BeautifulSoup(r.text, "lxml")

    # 1) Find the main article body
    body = soup.select_one("div.article-body")
    thumbnail_url = None
    body_text = None
    meta_description = None

    if body:
        # a) Thumbnail within figure.article-figure > div.figure-img > img
        img = body.select_one("figure.article-figure div.figure-img img")
        if img:  # img 태그가 있으면 src 후보를 모읍니다.
            thumbnail_url = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-original")
                or None
            )

        # b) Remove non-textual or irrelevant blocks
        for tag in body.select("figure, script, style, aside"):
            tag.decompose()

        # c) Prefer paragraph/list items; fallback to all text
        parts = []
        for el in body.select("p, li"):
            t = el.get_text(" ", strip=True)
            if t:
                parts.append(t)
        if not parts:
            raw = body.get_text("\n", strip=True)
            if raw:
                parts = [raw]

        if parts:
            # 문단 사이에 빈 줄을 넣어 가독성을 높입니다.
            body_text = "\n\n".join(text_collapse(p) for p in parts if p)

    # 대표 이미지가 없으면 og:image 메타 태그를 이용합니다.
    if not thumbnail_url:
        og = soup.select_one('meta[property="og:image"]')
        if og and og.get("content"):
            thumbnail_url = og["content"].strip() or None

    og_desc = soup.select_one('meta[property="og:description"]') or soup.select_one('meta[name="description"]')
    if og_desc and og_desc.get("content"):
        meta_description = clean_text(og_desc["content"])

    return (thumbnail_url, body_text, meta_description)


# --- [RSS에서 항목 뽑기] ---
def fetch_rss_items(limit: int | None = None):
    """RSS 피드를 내려받아 title/link/author/pubDate만 남긴 리스트를 반환한다."""
    resp = session.get(RSS_URL, timeout=15)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)

    items = []
    for entry in feed.entries:
        title = sanitize_title(entry.get("title", "").strip())
        link = entry.get("link", "").strip()
        author = entry.get("author", None)
        pubdate = entry.get("published", None) or entry.get("pubDate", None)

        if not link:
            continue

        items.append({
            "title": title,
            "link": link,
            "author": author,
            "pubDate": pubdate,
        })

        if limit and len(items) >= limit:
            break
    return items

# --- [메인 루틴] ---
def main():
    """스크립트를 직접 실행했을 때 RSS 항목을 순회하며 JSON Lines를 출력한다."""
    ap = argparse.ArgumentParser(description="Scrape Hankyung IT RSS + article details")
    ap.add_argument("--limit", type=int, default=10, help="Number of RSS items to process")
    args = ap.parse_args()

    rss_items = fetch_rss_items(limit=args.limit)  # RSS에서 지정한 개수만큼 읽어옵니다.

    for it in rss_items:  # 각 RSS 항목을 순회합니다.
        link = it["link"]
        title = it["title"]
        author = it.get("author")
        pubdate = it.get("pubDate")
        entry_summary_html = it.get("summary") or it.get("description")
        entry_summary_text = html_to_text(entry_summary_html)

        if not is_relevant(title, entry_summary_text):
            continue

        published_at = parse_pubdate_to_utc_iso(pubdate)  # UTC ISO
        date_kst = kst_bucket_date_from_utc_iso(published_at)  # YYYY-MM-DD (KST)

        # 기사 페이지에서 대표 이미지와 본문을 추출합니다.
        thumb, body, meta_desc = extract_article_details(link)
        summary = summarize_text(body) if body else None
        if not summary:
            summary = summarize_text(entry_summary_text)
        if not summary and meta_desc:
            summary = summarize_text(meta_desc)
        if not body and entry_summary_text:
            body = entry_summary_text
        if not body and meta_desc:
            body = meta_desc
        body = body or entry_summary_text or meta_desc or ""

        if len(body.strip()) < 150:
            continue

        if not summary:
            summary = "요약 없음"

        if not is_relevant(title, summary, body):
            continue

        doc = {
            "id": sha1_hex(link),
            "source": SOURCE_NAME,
            "title": title,
            "link": link,
            "author": author,
            "published_at": published_at,  # UTC ISO8601
            "date": date_kst,              # KST bucket
            "thumbnail": thumb,
            "summary": summary,
            "body": body,
            "category": categorize(title),
        }

        print(json.dumps(doc, ensure_ascii=False))


if __name__ == "__main__":
    main()
