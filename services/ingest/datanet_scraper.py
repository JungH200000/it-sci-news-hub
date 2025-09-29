# datanet_scraper.py
"""DataNet RSS를 수집해 Supabase 적재용 JSON Lines 형태로 가공하는 스크립트."""
# Fields: id, source, title, link, author, published_at(UTC ISO), date(KST), thumbnail, summary, body, category

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import feedparser
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

# --- [상수 설정] ---
RSS_URL = "https://www.datanet.co.kr/rss/allArticle.xml"
SOURCE_NAME = "DataNet"
KST = ZoneInfo("Asia/Seoul")

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

def sanitize_title(value: str) -> str:
    """RSS 제목에서 이스케이프 문자와 큰따옴표를 제거한다."""

    if not value:
        return ""
    cleaned = value.replace("\\", "")
    cleaned = cleaned.replace('"', "")
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
    """블랙리스트 키워드가 포함되지 않은 경우에만 True를 반환한다."""

    for raw in texts:
        normalized = _normalize(raw)
        if not normalized:
            continue
        for keyword in BLACKLIST_KEYWORDS:
            if keyword in normalized:
                return False
    return True


SENTENCE_ENDINGS = ["다.", "다?", "다!", ".", "!", "?", "…"]


def ensure_sentence_boundary(text: str, truncated: bool = False) -> str:
    """요약문이 문장 중간에서 끊기지 않도록 마무리를 다듬는다."""

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
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    try:
        dt = datetime.strptime(pubdate.strip(), "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=KST)
        return dt.astimezone(timezone.utc).isoformat()
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


def text_collapse(value: str) -> str:
    """여러 공백/탭/제어 문자를 한 칸 공백으로 줄이고 양끝 공백 제거(본문 출력 품질 개선)."""
    return re.sub(r"[ \t\r\f\v]+", " ", value).strip()


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return text_collapse(value)


def html_to_text(html: str | None) -> str:
    """HTML 문자열에서 태그를 제거하고 순수 텍스트만 반환한다."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    return clean_text(soup.get_text(" ", strip=True))


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

# --- [기사 페이지 파싱] ---
def extract_article_details(article_url: str) -> tuple[str | None, str | None, str | None]:
    """DataNet 기사 페이지에서 (대표 이미지, 본문 텍스트, 메타 설명)을 추출한다."""

    try:
        resp = session.get(article_url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[warn] failed to fetch article: {article_url} ({exc})", file=sys.stderr)
        return None, None, None

    # BeautifulSoup의 lxml parser를 사용
    soup = BeautifulSoup(resp.text, "lxml")

    # 1) 메인 기사 본문(body) 찾기
    body = soup.select_one("#article-view-content-div") or soup.select_one("div.article-body")
    thumbnail_url = None
    body_text = None
    meta_description = None

    if body:
        # a) 이미지(Thumbnail)
        img = body.select_one("div.IMGFLOATING img") or soup.select_one("div.IMGFLOATING img")
        if img: # img 태그가 있으면 src 후보를 모읍니다.
            thumbnail_url = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-original")
                or None
            )

        # b) 텍스트가 아닌 블록이나, 본문과 무관한 요소 제거
        for tag in body.select("figure, script, style, aside"):
            tag.decompose()

        # c) 가능하다면 `<p>` 태그나 `<li>` 태그 안의 텍스트만 우선적으로 사용, 그런 게 없으면 본문 전체 텍스트 수집
        parts = []
        for el in body.select("p, li"):
            text = el.get_text(" ", strip=True)
            if text:
                parts.append(text)

        if not parts:
            # `parts`가 빈 리스트 -> body에 저장된 모든 텍스트를 긁어와서 `\n` 단위로 붙여 넣음
            raw = body.get_text("\n", strip=True)
            if raw:
                # 위 코드(`if not parts:`)의 결과를 `parts`에 한 덩어리로 저장
                parts = [raw]

        # `parts` 리스트 안에는 문단별 텍스트 존재
        if parts:
            # `text_collapse(p)` 문단 안에서 중복 공백, 탭 간은 걸 한 칸 공백으로 정리
            # 문단 사이에 빈 줄을 넣어 가독성을 높임
            body_text = "\n\n".join(text_collapse(p) for p in parts if p)

    # 대표 이미지가 없으면 og:image 메타 태그를 이용합니다.
    if not thumbnail_url:
        meta_img = soup.select_one("meta[property='og:image']")
        if meta_img and meta_img.get("content"):
            thumbnail_url = meta_img["content"].strip() or None

    # 메타 설명(요약 텍스트) 찾기
    og_desc = soup.select_one("meta[property='og:description']") or soup.select_one("meta[name='description']")
    if og_desc and og_desc.get("content"):
        meta_description = clean_text(og_desc["content"])

    return thumbnail_url, body_text, meta_description

# --- [RSS에서 항목 뽑기] ---
def fetch_rss_items(limit: int | None = None) -> list[dict]:
    """RSS 피드를 내려받아 title/link/author/pubDate만 남긴 리스트를 반환한다."""

    resp = session.get(RSS_URL, timeout=30)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)

    items: list[dict] = []
    for entry in feed.entries:
        title = sanitize_title(entry.get("title", "").strip())
        link = entry.get("link", "").strip()
        author = entry.get("author")
        pubdate = entry.get("published") or entry.get("pubDate")
        summary_html = entry.get("summary") or entry.get("description")

        if not link:
            continue

        items.append(
            {
                "title": title,
                "link": link,
                "author": author,
                "pubDate": pubdate,
                "entry_summary": summary_html,
            }
        )

        if limit and len(items) >= limit:
            break

    return items

# --- [메인 루틴] ---
def main() -> None:
    """스크립트를 직접 실행했을 때 RSS 항목을 순회하며 JSON Lines를 출력한다."""

    # "이 프로그램이 어떤 옵션을 받는지”를 설명하는 최상위 파서(메뉴판) 를 만듦.
    # description= 은 -h/--help로 도움말을 볼 때 맨 위에 나오는 설명 문구
    parser = argparse.ArgumentParser(description="Scrape DataNet RSS + article details")

    # `--limit` 옵션으로 RSS에서 최대 몇 개를 처리할지 정함(default=10개)
    parser.add_argument("--limit", type=int, default=10, help="Number of RSS items to process")

    #  사용자가 터미널에 입력한 옵션을 읽어와서 `args`에 담음
    args = parser.parse_args()

    # `fetch_rss_items()`가 RSS 문서를 내려 받아 title/link/author/pubDate만 남긴 리스트를 반환
    rss_items = fetch_rss_items(limit=args.limit) # RSS에서 지정한 개수만큼 읽어옵니다.

    for item in rss_items: # 각 RSS 항목을 순회합니다.
        # RSS 항목에서 필요한 필드를 꺼냄
        link = item["link"]
        title = item["title"]
        author = item.get("author")
        pubdate = item.get("pubDate")
        entry_summary_html = item.get("entry_summary")
        entry_summary_text = html_to_text(entry_summary_html)

        # 제목/요약 텍스트에 블랙리스트 키워드가 있으면 건너뜀
        if not is_relevant(title, entry_summary_text):
            continue

        # RSS의 `pybDate`를 UTC ISO 문자열로 변환
        published_at = parse_pubdate_to_utc_iso(pubdate)  # UTC ISO

        # 같은 시각을 KST 날짜(YYYY-MM-DD)로 계산 -> UI 사이드바/일별 목록에 쓰기 좋게 `date`로 저장
        date_kst = kst_bucket_date_from_utc_iso(published_at) # YYYY-MM-DD (KST)

        # 기사 페이지에서 대표 이미지와 본문을 추출합니다.
        thumbnail, body, meta_desc = extract_article_details(link)

        # 요약 만들기 - 규칙 기반
        # 우선 순위: 본문 ➡️ RSS 요약 텍스트 ➡️ 메타 설명
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

        # 본문이 150자 이하면 건너뜀
        if len(body.strip()) < 150:
            continue

        # 요약이 없으면 "요약 없음"으로 표시
        if not summary:
            summary = "요약 없음"

        # 본문/요약 보정 후 블랙리스트 검사 후 비관련 기사 제거
        if not is_relevant(title, summary, body):
            continue

        doc = {
            "id": sha1_hex(link),
            "source": SOURCE_NAME,
            "title": title,
            "link": link,
            "author": author,
            "published_at": published_at,
            "date": date_kst,
            "thumbnail": thumbnail,
            "summary": summary,
            "body": body,
            "category": categorize(title),
        }

        # 한 줄 JSON으로 출력
        print(json.dumps(doc, ensure_ascii=False))


if __name__ == "__main__":
    main()
