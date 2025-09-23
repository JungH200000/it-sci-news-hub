# -*- coding: utf-8 -*-
import re
import sys
import json
import requests
from bs4 import BeautifulSoup, Tag

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE_DETAIL = "https://scienceon.kisti.re.kr/trendPromo/PORTrendPromoDtl.do?trendPromoNo={no}"

# ---------- text utils ----------
def clean_text(s: str) -> str:
    if not s: return ""
    s = s.replace("\xa0", " ").replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def looks_like_title(t: str) -> bool:
    if not t or len(t) < 4: return False
    if t.lower() in {"new", "(new)"}: return False
    return True

def smart_title_clean(s: str) -> str:
    # 불릿 이후/날짜 꼬리표 제거
    s = clean_text(s)
    if "ㆍ" in s: s = s.split("ㆍ", 1)[0].strip()
    s = re.sub(r"\(\s*[^()]*\d{2,4}[.\-/]\d{1,2}([.\-/]\d{1,2})?[^()]*\)\s*$", "", s).strip()
    if len(s) > 180: s = s[:180].rstrip()
    return s

def strip_anchor_text(node: Tag) -> str:
    soup = BeautifulSoup(str(node), "lxml")
    for a in soup.find_all("a"): a.decompose()
    return soup.get_text(" ", strip=True)

def has_korean(t: str) -> bool:
    return bool(re.search(r"[가-힣]", t or ""))

# ---------- page structure helpers ----------
def is_title_paragraph(p: Tag) -> bool:
    return (p.name == "p" and "MsoNormal" in (p.get("class") or []) and p.find("a", href=True) is not None)

def extract_link_from_p(p: Tag) -> str:
    for a in p.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if href.startswith("http"): return href
    return ""

def extract_title_from_p(p: Tag) -> str:
    # a가 들어있는 가장 가까운 컨테이너(span/strong/em) 우선
    a = p.find("a", href=True)
    if a:
        cur, depth = a.parent, 0
        while isinstance(cur, Tag) and depth < 5:
            if cur.name in {"span", "strong", "em"}:
                t = smart_title_clean(strip_anchor_text(cur))
                if looks_like_title(t): return t
            if cur == p: break
            cur = cur.parent; depth += 1
    # p에서 a 제거
    t2 = smart_title_clean(strip_anchor_text(p))
    if looks_like_title(t2): return t2
    # 최후: p 전체
    title = smart_title_clean(p.get_text(" ", strip=True))
    # 카테고리 프리픽스 제거
    title = strip_prefix_category(title)
    return title

def strip_prefix_category(title: str) -> str:
    """
    제목 맨 앞의 '- ( ... )' 또는 '( ... )' 패턴을 제거.
    예: '- ( 💥 양자 ) 거시세계...' → '거시세계...'
    """
    # 맨 앞의 대시와 괄호 블록 제거
    title = re.sub(r"^\s*-\s*\([^)]*\)\s*", "", title)
    title = re.sub(r"^\s*\([^)]*\)\s*", "", title)
    return title.strip()


# ---------- summary finder ----------
BULLET_START = re.compile(r"^[\s\u00A0]*[ㆍ·•\-]+[\s\u00A0]*")

def split_first_bullet_line(text: str) -> str:
    """
    긴 문단에 불릿이 여러 개 이어질 때, '첫 불릿'만 한 줄 요약으로.
    예: 'ㆍ ... - ㆍ ...' 형태 → 첫 불릿 조각만.
    """
    # 먼저 맨 앞 불릿 제거
    t = BULLET_START.sub("", text).strip()
    # 다음 불릿/대시 앞까지 자르기
    t = re.split(r"\s(?:[ㆍ·•\-]\s)", t, maxsplit=1)[0]
    return clean_text(t)

def find_summary_between(root: Tag, start: Tag, end: Tag | None) -> str:
    """
    start(제목 p) 이후부터 end(다음 제목 p) 이전까지 범위를 훑어 요약 후보를 찾는다.
    우선순위:
      1) 불릿 포함 p (한글 우선)
      2) 링크 없는 14px 스타일 p (한글 우선)
      3) 링크 없는 일반 p (한글 우선, 10~300자)
    없으면 빈 문자열
    """
    # 후보 버킷
    bullet_ko = None; bullet_any = None
    body14_ko = None; body14_any = None
    body_ko = None; body_any = None

    # next_elements를 써서 h2 경계도 통과
    for el in start.next_elements:
        if el is end: break
        if not isinstance(el, Tag): continue

        # 다음 제목 p를 만나면 종료
        if is_title_paragraph(el) and el is not start:
            break

        if el.name == "p" and "MsoNormal" in (el.get("class") or []):
            has_link = el.find("a", href=True) is not None
            raw = el.get_text(" ", strip=True)
            txt = clean_text(raw)

            # 1) 불릿 케이스
            if BULLET_START.search(txt):
                one = split_first_bullet_line(txt)
                if has_korean(one) and not bullet_ko: bullet_ko = one
                if not bullet_any: bullet_any = one
                continue

            # 2) 14px 본문 & 링크 없음
            if not has_link and "font-size: 14px" in (el.get("style") or ""):
                if has_korean(txt) and not body14_ko: body14_ko = txt
                if not body14_any: body14_any = txt
                continue

            # 3) 일반 본문 & 링크 없음 (너무 긴 건 제외)
            if not has_link and 10 <= len(txt) <= 300:
                if has_korean(txt) and not body_ko: body_ko = txt
                if not body_any: body_any = txt

    return bullet_ko or body14_ko or body_ko or bullet_any or body14_any or body_any or ""

# ---------- optional external fallback ----------
def fetch_fallback_summary_from_link(link: str) -> str:
    try:
        rr = requests.get(link, headers=HEADERS, timeout=10)
        rr.raise_for_status()
    except Exception:
        return ""
    if not rr.encoding or rr.encoding.lower() in ("iso-8859-1", "us-ascii"):
        rr.encoding = rr.apparent_encoding
    ss = BeautifulSoup(rr.text, "lxml")
    for sel in ["meta[property='og:description'][content]", "meta[name='description'][content]"]:
        m = ss.select_one(sel)
        if m and m.get("content"):
            return clean_text(m["content"])
    return ""

## ---------- date and source ----------

def extract_date_and_source(raw_text: str) -> tuple[str, str]:
    """
    (동아사이언스 / 2025.09.18.) 같은 꼬리표에서 source와 date 추출
    return (date, source) / 없으면 ("","")
    """
    m = re.search(r"\(([^()/]+)\s*/\s*(\d{2,4})[.\-](\d{1,2})[.\-](\d{1,2})", raw_text)
    if not m:
        return "", ""
    source = m.group(1).strip()
    yyyy, mm, dd = int(m.group(2)), int(m.group(3)), int(m.group(4))
    # 연도 보정: 0~99 → 2000+연도 (예: 25 → 2025), 100~999 → 2000+연도가 과하면 상황에 맞게 조정
    if yyyy < 100:
        yyyy += 2000
    elif 100 <= yyyy < 1000:
        # 대부분 오탈자(예: 025) 케이스만 존재하므로 100~999는 드물다.
        # 필요하면 규칙 확장 가능. 일단 2000대가 아니면 2000 더하지 않음.
        pass

    date_str = f"{yyyy:04d}-{mm:02d}-{dd:02d}"
    return date_str, source

# 범위에서 (source / yyyy.mm.dd) 꼬리표를 찾아서 반환
DATE_SOURCE_PAT = re.compile(
    r"[（(]\s*([^()（）/|]+?)\s*[/|]\s*(\d{2,4})[.\-](\d{1,2})[.\-](\d{1,2})\.?\s*[)）]"
)

def extract_date_source_near(root: Tag, start: Tag, end: Tag | None) -> tuple[str, str]:
    """
    start(제목 p) 이후 ~ end(다음 제목 p) 이전 범위에서
    '(출처 / YYYY.MM.DD.)' 패턴을 찾아 (date, source) 반환.
    못 찾으면 ("","")
    """
    for el in start.next_elements:
        if el is end:
            break
        if not isinstance(el, Tag):
            continue
        if is_title_paragraph(el) and el is not start:
            break

        # 텍스트 많은 p/span에만 시도
        if el.name in {"p", "span"}:
            raw = el.get_text(" ", strip=True)
            m = DATE_SOURCE_PAT.search(raw)
            if m:
                source = m.group(1).strip()
                yyyy, mm, dd = int(m.group(2)), int(m.group(3)), int(m.group(4))
                date_str = f"{yyyy:04d}-{mm:02d}-{dd:02d}"  # KST 버킷 YYYY-MM-DD
                return date_str, source
    return "", ""


# ---------- main parse ----------
def parse_detail(detail_url: str, use_external_fallback: bool = False):
    r = requests.get(detail_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() in ("iso-8859-1", "us-ascii"):
        r.encoding = r.apparent_encoding

    soup = BeautifulSoup(r.text, "lxml")
    root = soup.select_one("div.board-view-content")
    if not root: raise RuntimeError("board-view-content 영역을 찾지 못했습니다.")

    # 1) 제목 p 리스트 만들기
    title_ps: list[Tag] = [p for p in root.find_all("p", class_="MsoNormal") if is_title_paragraph(p)]

    items = []
    for i, p in enumerate(title_ps):
        link = extract_link_from_p(p)
        if not link.startswith("http"): continue

        # 제목 원문 텍스트
        title_raw = p.get_text(" ", strip=True)

        # 날짜 + 출처 꼬리표에서 추출
        date, source = extract_date_and_source(title_raw)

        # 제목 정리
        title = smart_title_clean(title_raw)
        title = strip_prefix_category(title)

        if not looks_like_title(title): continue

        # 2) 다음 제목 p를 경계로 요약 탐색
        end = title_ps[i+1] if i+1 < len(title_ps) else None
        summary = find_summary_between(root, p, end)

        # 🔹 요약 범위에서 날짜/출처 스캔 (제목 p 안에 없을 때 대비)
        date, source = extract_date_source_near(root, p, end)

        # 그래도 못 찾았고, 제목 raw에 있는 경우엔 보조 추출 (기존 함수 그대로 활용 가능)
        if not date or not source:
            title_raw = p.get_text(" ", strip=True)
            d2, s2 = extract_date_and_source(title_raw)
            if d2 and s2:
                date, source = d2, s2

        # 3) 정말 비면(그리고 원할 때만) 외부 메타 fallback
        if not summary and use_external_fallback:
            summary = fetch_fallback_summary_from_link(link)
        
        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "week": date,
            "source": source
        })

    return items

# ---------- list page (목록) -> detail nos ----------

LIST_URL = "https://scienceon.kisti.re.kr/trendPromo/PORTrendPromoList.do"

JS_NO_RE = re.compile(r"fn_moveTrendPromoDtl\('(\d+)'\)")

def fetch_html(url: str, params: dict | None = None) -> str:
    r = requests.get(url, params=params or {}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() in ("iso-8859-1", "us-ascii"):
        r.encoding = r.apparent_encoding
    return r.text

def parse_list_page(html: str) -> list[dict]:
    """
    목록 페이지에서 최신 게시글들의 trendPromoNo, 리스트 타이틀, 리스트 날짜 추출
    return: [{"no":"260","list_title":"[9월 4주차] 금주의 과학기술뉴스(1)","list_date":"2025-09-23"}, ...]
    """
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("table.board-list-tbl tbody tr")
    out = []
    for tr in rows:
        a = tr.select_one("td.subject a[href]")
        if not a:
            continue
        m = JS_NO_RE.search(a.get("href", ""))
        if not m:
            continue
        no = m.group(1)
        list_title = clean_text(a.get_text(" ", strip=True))
        list_date = clean_text((tr.select_one("td.date") or {}).get_text(" ", strip=True) if tr.select_one("td.date") else "")

        pm = re.search(r"\[([0-9]+월\s*[0-9]+주차)\]", list_title)
        period_label = pm.group(1) if pm else list_title

        out.append({
            "no": no, 
            "period_label": period_label, 
            "list_date": list_date
        })
    return out

def crawl_from_list(pages: int = 1, limit: int | None = None, use_external_fallback: bool = False) -> list[dict]:
    """
    목록 페이지를 앞에서부터 `pages` 장 훑어 최신 글들의 상세를 크롤링.
    - pages: 1이면 첫 페이지(최신 10개)만
    - limit: 총 수집 상한 (None이면 제한 없음)
    """
    # KISTI는 보통 pageIndex 파라미터로 페이징 (없으면 1페이지)
    all_list_items: list[dict] = []
    for page in range(1, pages + 1):
        html = fetch_html(LIST_URL, params={"pageIndex": page})
        items = parse_list_page(html)
        if not items:
            break
        all_list_items.extend(items)
        if limit and len(all_list_items) >= limit:
            all_list_items = all_list_items[:limit]
            break

    results: list[dict] = []
    for li in all_list_items:
        detail_url = BASE_DETAIL.format(no=li["no"])
        detail_items = parse_detail(detail_url, use_external_fallback=use_external_fallback)
        # 해당 상세 글 안에 여러 기사(title/link/summary…)가 들어있으므로 그대로 병합
        for d in detail_items:
            # 상세에서 date/source를 못 잡았으면 리스트 날짜를 보조로 사용 (YYYY-MM-DD 또는 YYYY.MM.DD 둘 다 커버)
            if not d.get("date"):
                # list_date가 'YYYY-MM-DD' 또는 'YYYY.MM.DD'일 수 있음 → '-' 포맷으로 보정
                ld = li.get("list_date", "")
                if re.match(r"^\d{4}[.\-]\d{2}[.\-]\d{2}$", ld):
                    d["date"] = ld.replace(".", "-")
            # 원하면 목록 제목도 메타로 남겨두기
            d.setdefault("period_label", li["period_label"])
            d.setdefault("trendPromoNo", li["no"])
            results.append(d)
    return results


# ---------- CLI ----------

def print_usage():
    print("Usage:")
    print("  python science_on_scraper.py list               # 최신 10개(1페이지) 상세 크롤링")
    print("  python science_on_scraper.py list 2             # 2페이지(최대 20개) 크롤링")
    print("  python science_on_scraper.py list 1 30          # 1페이지에서 최대 30개(넘치면 다음 페이지로) 크롤링")
    print("  python science_on_scraper.py 260                # 단일 상세 페이지만 (기존 동작)")

def main():
    # 기존 단일 상세 동작 유지 + 목록 모드 추가
    if len(sys.argv) >= 2 and sys.argv[1].lower() == "list":
        pages = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
        limit = int(sys.argv[3]) if len(sys.argv) >= 4 else None
        data = crawl_from_list(pages=pages, limit=limit, use_external_fallback=False)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # 단일 상세 (기존)
    no = sys.argv[1] if len(sys.argv) >= 2 else "260"
    url = BASE_DETAIL.format(no=no)
    data = parse_detail(url, use_external_fallback=False)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

