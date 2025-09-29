# naver_tech_scraper.py
"""네이버 IT/과학 섹션을 스크래핑해 Supabase 적재용 JSON Lines를 생성하는 스크립트."""
# Fields: id, source, title, link, author, published_at(UTC ISO), date(KST), thumbnail, summary, body, category

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup, NavigableString
# BeautifulSoup은 여러 파서를 지원하지만 여기서는 'lxml'을 사용

# --- [상수 설정] ---
NAVER_SECTION_URL = "https://news.naver.com/section/105"
SOURCE_NAME = "네이버 IT/과학"
KST = ZoneInfo("Asia/Seoul")
REQUEST_TIMEOUT = 20

# --- [HTTP 세션 준비] ---
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))
session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
)

# --- [카테고리 규칙: 기본값 + 제목 키워드 덮어쓰기] ---
CATEGORY_DEFAULT = "IT/과학"
CATEGORY_RULES = [
    (re.compile(r"(AI|인공지능|GPT|LLM|딥러닝)", re.I), "AI"),
    (re.compile(r"(카카오|kakao|클라우드|국가정보자원관리원|인프라|데이터센터)", re.I), "IT"),
    (re.compile(r"(보안|해킹|유출|취약|랜섬)", re.I), "보안"),
    (re.compile(r"(반도체|칩|파운드리|퀀텀|엔비디아|양자)", re.I), "반도체"),
    (re.compile(r"(로봇|로보틱스)", re.I), "로봇"),
    (re.compile(r"(생명|제약|백신|유전체|미생물|바이오|신약|항암제|안약|장기|장염|질환|척수|미트콘드리아|위암|간암|간염|근육|고혈압|수면|DNA|RNA|세포|머리카락|여드름|알츠하이머|항생제|바이러스|박테리아|알테오젠|셀트리온|팬젠|임상|의약|처방|암치료기기|포도당|유전)", re.I), "생명과학"),
    (re.compile(r"(배터리|전지|탑머티리얼|양극재)", re.I), "배터리"),
]

BLACKLIST_KEYWORDS = {
    "부동산", "아파트", "채권", "주식", "환율", "외환", "물가", "금리",
    "취업", "채용", "노동", "고용", "인사", "임금", "연봉",
    "규제", "과징금", "제재", "검찰", "경찰", "사건", "소송", "재판",
    "선거", "정치", "외교", "안보", "헌신", "관세", "영양제", "외래환자",
    "LCK", "가족 친화 경영", "전산시스템", "다이소", "젠지", "박카스", 
    "폭발한", "무서워", "스크래치", "창업자", "붉은사막", "RPG", "서브컬쳐",
    "플로깅", "헌혈", "화백", "티맵", "위약금", "트럼프", "대금", "사생활",
    "영입", "버스킹", "뿔난", "화난", "사의", "워라벨"
}

SENTENCE_ENDINGS = ["다.", "다?", "다!", ".", "!", "?", "…"]


def sanitize_title(value: str | None) -> str:
    """RSS에서 내려온 제목에서 이스케이프 문자와 큰따옴표를 제거한다."""
    if not value:
        return ""
    cleaned = value.replace("\\", "").replace('"', "")
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
    for raw in texts:
        normalized = _normalize(raw)
        if not normalized:
            continue
        for keyword in BLACKLIST_KEYWORDS:
            if keyword in normalized:
                return False
    return True


def text_collapse(value: str) -> str:
    """여러 공백/탭/제어 문자를 한 칸 공백으로 줄이고 양끝 공백 제거(본문 출력 품질 개선)."""
    return re.sub(r"[\s\u00A0]+", " ", value).strip()


def ensure_sentence_boundary(text: str, truncated: bool = False) -> str:
    """요약이 문장 중간에서 끊기지 않도록 마지막 완결 문장까지만 남긴다."""
    text = (text or "").strip()
    if not text:
        return text
    
    # 문장 끝 위치 찾기
    end_positions: list[int] = []
    for ending in SENTENCE_ENDINGS:
        # 문자열에서 기호가 마지막으로 나온 위치를 찾음
        idx = text.rfind(ending)
        if idx != -1:
            # 찾으면 기호의 끝 인덱스를 `end_positions`에 저장
            end_positions.append(idx + len(ending))
    
    # 마지막 문장 끝까지 자르기
    if end_positions:
        # 가장 뒤쪽 문장 끝 위치를 기준으로 잘라냄
        return text[: max(end_positions)].strip()
    if truncated:
        # 문장 끝 기호가 전혀 없고 `truncated=True`라면 마침표 등을 제거하고 `...`을 붙여 여기서 잘렸다고 표시
        return text.rstrip(".") + "…"
    return text

# ---- Utils ----
def sha1_hex(value: str) -> str:
    """문자열을 SHA1 해시로 40자리 헥사 문자열로 변환(고유 ID 생성 용도)."""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def summarize_text(text: str, max_sentences: int = 3, max_chars: int = 180) -> str | None:
    """간단한 규칙 기반 요약: 앞쪽 문장 2~3개를 취하고 180자 내로 제한."""

    # 1. 입력 검사 ➡️ 텍스트가 비어있으면 `None`
    if not text:
        return None
    
    # 2. 줄바꿈을 공백으로 변경 후 `. ? !` 같은 문장 마침 기호를 기준으로 문장을 나눔
    normalized = text.replace("\n", " ")
    candidates = re.split(r"(?<=[.!?\u3002\uFF01\uFF1F])\s+", normalized)

    # 3. 앞 쪽 몇 문장만 추출
    sentences: list[str] = []
    for cand in candidates:
        # 공백 정리
        cleaned = text_collapse(cand)
        if cleaned:
            sentences.append(cleaned)
        if len(sentences) >= max_sentences:
            # 앞에서 최대 `max_sentences`개만 모음 ➡️ default = 3 문장
            break
    
    if not sentences:
        return None
    
    # 4. 길이 제한(180자) 안에서 합치기
    selected: list[str] = []
    truncated = False
    for sent in sentences:
        candidate = " ".join(selected + [sent]) if selected else sent
        if len(candidate) > max_chars:
            truncated = True
            break
        selected.append(sent)

    # 5. 최종 요약 문자열 만들기
    if not selected:
        # 문장을 하나도 못 붙힘 ➡️ 첫 문장 잘라서 사용
        truncated = True
        summary = sentences[0][:max_chars].strip()
    else:
        # 문장을 붙였는데 180자를 넘으면 앞 부분만 잘라냄
        summary = " ".join(selected).strip()
        if len(summary) > max_chars:
            truncated = True
            summary = summary[:max_chars].strip()

    # 6. 문장 끝 경계 정리
    # 요약 문장이 중간에서 끊기지 않도록 `ensure_sentence_boundary`로 정리
    summary = ensure_sentence_boundary(summary, truncated)

    # 실패하면 첫 문장을 잘라서라도 반환
    if not summary:
        fallback = ensure_sentence_boundary(sentences[0][:max_chars].strip(), True)
        return fallback or None
    return summary


def parse_article_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=KST)
    except Exception:
        return None


def to_utc_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.astimezone(timezone.utc).isoformat()


def kst_bucket_date(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.date().isoformat()


def extract_body(soup: BeautifulSoup) -> str | None:
    container = soup.select_one("div#newsct_article")
    article = None
    if container and container.name == "article":
        article = container
    elif container:
        article = container.select_one("article#dic_area")
    if not article:
        article = soup.select_one("article#dic_area")
    if not article:
        return None

    for tag in article.select(
        "script, style, aside, figure, table, .media_end_copyright, .media_end_summary"
    ):
        tag.decompose()

    parts: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        merged = text_collapse(" ".join(buffer))
        if merged:
            parts.append(merged)
        buffer.clear()

    for node in article.children:
        if isinstance(node, NavigableString):
            text = text_collapse(str(node))
            if text:
                buffer.append(text)
        else:
            name = getattr(node, "name", "")
            if name and name.lower() == "br":
                flush()
            else:
                flush()

    flush()

    if not parts:
        raw_text = article.get_text(" ", strip=True)
        if not raw_text:
            return None
        return text_collapse(raw_text)

    return "\n\n".join(parts)


def extract_thumbnail(soup: BeautifulSoup) -> str | None:
    img = soup.select_one("img#img1")
    if img:
        for attr in ("src", "data-src", "data-origin", "data-original"):
            value = img.get(attr)
            if value:
                return value.strip()
    meta = soup.select_one("meta[property='og:image']")
    if meta and meta.get("content"):
        return meta["content"].strip() or None
    return None


def is_article_url(url: str) -> bool:
    lowered = url.lower()
    if "/comment/" in lowered:
        return False
    return "/article/" in lowered


def extract_links(limit: int) -> list[str]:
    try:
        resp = session.get(NAVER_SECTION_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch listing page: {exc}") from exc
    soup = BeautifulSoup(resp.text, "lxml")
    anchors: list[str] = []
    containers = soup.select("div.section_latest_article._CONTENT_LIST._PERSIST_META")
    if not containers:
        containers = soup.select("div.section_latest_article")
    for block in containers:
        for anchor in block.select("div.sa_text a[href]"):
            href = anchor.get("href")
            if not href:
                continue
            href = href.strip()
            if not href:
                continue
            if href.startswith("//"):
                href = f"https:{href}"
            elif href.startswith("/"):
                href = urljoin(NAVER_SECTION_URL, href)
            if not is_article_url(href):
                continue
            anchors.append(href)
    unique: list[str] = []
    seen: set[str] = set()
    for link in anchors:
        if link in seen:
            continue
        seen.add(link)
        unique.append(link)
        if len(unique) >= limit:
            break
    return unique


def scrape_article(url: str) -> dict | None:
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[warn] failed to fetch article: {url} ({exc})", file=sys.stderr)
        return None
    soup = BeautifulSoup(resp.text, "lxml")
    title_el = soup.select_one("h2#title_area span")
    title = sanitize_title(title_el.get_text(strip=True) if title_el else "")
    if not title:
        print(f"[warn] missing title: {url}", file=sys.stderr)
        return None
    author_el = soup.select_one("em.media_end_head_journalist_name")
    author = text_collapse(author_el.get_text(strip=True)) if author_el else None
    date_el = soup.select_one("span.media_end_head_info_datestamp_time._ARTICLE_DATE_TIME")
    published_kst = parse_article_datetime(date_el.get("data-date-time") if date_el else None)
    published_utc = to_utc_iso(published_kst)
    date_bucket = kst_bucket_date(published_kst)
    if not published_utc or not date_bucket:
        return None
    thumbnail = extract_thumbnail(soup)
    body = extract_body(soup)
    if not body or len(body) < 150:
        return None
    if not is_relevant(title, body):
        return None
    summary = summarize_text(body)
    if not summary:
        summary = "요약 없음"
    original_source_el = soup.select_one("span.media_end_linked_title_text")
    original_source = (
        text_collapse(original_source_el.get_text(strip=True)) if original_source_el else None
    )
    record = {
        "id": sha1_hex(url),
        "source": original_source or SOURCE_NAME,
        "distributor": SOURCE_NAME,
        "title": title,
        "link": url,
        "author": author,
        "published_at": published_utc,
        "date": date_bucket,
        "thumbnail": thumbnail,
        "summary": summary,
        "body": body,
        "category": categorize(title),
    }
    if original_source:
        record["original_source"] = original_source
    return record


def take(iterable: Iterable[str], limit: int) -> list[str]:
    items: list[str] = []
    for item in iterable:
        items.append(item)
        if len(items) >= limit:
            break
    return items

# --- [메인 루틴] ---
def main() -> None:
    # "이 프로그램이 어떤 옵션을 받는지”를 설명하는 최상위 파서(메뉴판) 를 만듦.
    # description= 은 -h/--help로 도움말을 볼 때 맨 위에 나오는 설명 문구
    parser = argparse.ArgumentParser(description="Scrape Naver IT/과학 articles")

    # `--limit` 옵션으로 최대 몇 개를 처리할지 정함(default=20개)
    parser.add_argument("--limit", type=int, default=20, help="Number of articles to process")

    #  사용자가 터미널에 입력한 옵션을 읽어와서 `args`에 담음
    args = parser.parse_args()

    try:
        links = extract_links(limit=max(args.limit, 1))
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    count = 0
    for link in take(links, args.limit):
        doc = scrape_article(link)
        if not doc:
            continue
        if not is_relevant(doc.get("title"), doc.get("summary"), doc.get("body")):
            # 제목/요약 텍스트에 블랙리스트 키워드가 있으면 건너뜀
            continue
        print(json.dumps(doc, ensure_ascii=False))
        count += 1
    if count == 0:
        print("[]", file=sys.stderr)


if __name__ == "__main__":
    main()
