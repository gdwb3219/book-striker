"""Build a large persona pool (100+ Korean YouTubers) automatically.

Pipeline:
  1. Collect channels: trending (mostPopular KR) + per-category channel search.
  2. Fetch channel stats + profile thumbnails; keep those over MIN_SUBS.
  3. Classify each channel into one of the content categories.
  4. Each category has a trait template + an Aladin book pool.
  5. Emit one persona per channel: category traits + a small per-channel offset
     (so same-category channels are still individually reachable) and 3 books
     rotated out of the category pool.

Run: python build_pool.py
Writes personas.json (schema unchanged, just many more personas).
"""

import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

YT_KEY = os.environ.get("YOUTUBE_API_KEY")
ALADIN_KEY = os.environ.get("ALADIN_TTB_KEY")
YT = "https://www.googleapis.com/youtube/v3"
ALADIN_URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
PERSONAS_PATH = BASE_DIR / "personas.json"

MIN_SUBS = 100_000
BOOKS_PER_PERSONA = 3
POOL_SIZE = 15  # Aladin books fetched per category

AXES = ["ei", "ns", "tf", "jp", "adv", "amb"]

# key -> config. traits = fan-persona trait template; kw = classify keywords;
# search = channel-search term; bookQuery = Aladin keyword.
CATEGORIES = {
    "economy": {
        "display": "경제·시사",
        "traits": {"ei": 0.0, "ns": 1.0, "tf": -1.2, "jp": 0.5, "adv": 0.2, "amb": 1.0},
        "fanLabel": "세상 돌아가는 원리가 궁금한 통찰가",
        "why": "복잡한 경제·사회 이슈를 큰 그림으로 꿰는 걸 즐겨요. 데이터로 세상을 읽는 당신에겐 지식이 곧 재미.",
        "kw": ["경제", "시사", "주식", "투자", "부동산", "뉴스", "재테크", "금융"],
        "search": "경제 유튜버",
        "bookQuery": "경제",
    },
    "travel": {
        "display": "여행·모험",
        "traits": {"ei": 0.5, "ns": 1.0, "tf": 0.3, "jp": -1.2, "adv": 2.0, "amb": 0.2},
        "fanLabel": "낯선 곳에서 자유를 느끼는 방랑자",
        "why": "계획보다 발길 닿는 대로. 새로운 풍경과 우연한 만남에서 살아있음을 느끼는 당신을 위한 이야기.",
        "kw": ["여행", "세계여행", "배낭", "트래블", "travel", "캠핑", "백패킹"],
        "search": "여행 유튜버",
        "bookQuery": "여행 에세이",
    },
    "growth": {
        "display": "자기계발·커리어",
        "traits": {"ei": 0.5, "ns": 0.5, "tf": 0.4, "jp": 1.2, "adv": 0.5, "amb": 2.0},
        "fanLabel": "더 나은 나를 설계하는 성장러",
        "why": "오늘보다 나은 내일을 그리는 사람. 목표와 루틴, 마인드셋에 진심인 당신을 위한 자기계발 명작들.",
        "kw": ["자기계발", "동기부여", "커리어", "성공", "생산성", "부자", "마인드"],
        "search": "자기계발 동기부여 유튜버",
        "bookQuery": "자기계발",
    },
    "science": {
        "display": "과학·지식",
        "traits": {"ei": -0.5, "ns": 1.5, "tf": -1.3, "jp": 0.2, "adv": 0.5, "amb": 0.6},
        "fanLabel": "우주와 원리에 설레는 지식덕후",
        "why": "'왜?'라는 질문을 멈추지 못하는 사람. 세상의 작동 원리를 파고들 때 가장 신나는 당신을 위한 과학 교양서.",
        "kw": ["과학", "지식", "우주", "물리", "역사", "교양", "다큐", "심리학"],
        "search": "과학 지식 유튜버",
        "bookQuery": "과학 교양",
    },
    "comedy": {
        "display": "코미디·예능",
        "traits": {"ei": 2.0, "ns": 0.5, "tf": 0.5, "jp": -1.0, "adv": 0.5, "amb": -0.5},
        "fanLabel": "웃음이 삶의 원동력인 흥부자",
        "why": "무겁게 사는 건 취향 아님. 유쾌하게 오늘을 즐기고 밈과 유머로 소통하는 당신을 위한 가벼운 명작들.",
        "kw": ["코미디", "예능", "개그", "웃긴", "밈", "몰카", "병맛", "유머"],
        "search": "코미디 예능 유튜버",
        "bookQuery": "유머 에세이",
    },
    "game": {
        "display": "게임·서브컬처",
        "traits": {"ei": -0.5, "ns": 1.5, "tf": 0.5, "jp": -0.5, "adv": 0.6, "amb": -0.4},
        "fanLabel": "상상의 세계를 사랑하는 몽상가",
        "why": "현실 너머의 세계관에 빠지는 걸 좋아하는 사람. 판타지와 반전, 새로운 우주를 탐험할 이야기들.",
        "kw": ["게임", "게이밍", "롤", "lol", "마인크래프트", "롤플레이", "스트리머", "방송"],
        "search": "게임 유튜버",
        "bookQuery": "판타지",
    },
    "food": {
        "display": "먹방·요리",
        "traits": {"ei": 0.5, "ns": -1.0, "tf": 1.5, "jp": -0.3, "adv": -0.5, "amb": -0.5},
        "fanLabel": "소소한 행복을 아는 따뜻한 사람",
        "why": "맛있는 거 먹을 때 제일 행복한 사람. 일상의 온기와 사람 사이 정을 소중히 여기는 당신을 위한 따뜻한 이야기.",
        "kw": ["먹방", "요리", "맛집", "레시피", "쿠킹", "mukbang", "먹스타"],
        "search": "먹방 요리 유튜버",
        "bookQuery": "요리",
    },
    "healing": {
        "display": "힐링·브이로그",
        "traits": {"ei": -1.5, "ns": -0.3, "tf": 1.5, "jp": -0.3, "adv": -1.2, "amb": -0.5},
        "fanLabel": "잔잔한 하루에서 위로받는 힐링러",
        "why": "조용한 아침, 따뜻한 차 한 잔의 여유를 아는 사람. 지친 마음을 다독여줄 잔잔하고 다정한 에세이들.",
        "kw": ["브이로그", "vlog", "힐링", "일상", "데일리", "소소", "감성"],
        "search": "일상 브이로그 유튜버",
        "bookQuery": "힐링 에세이",
    },
    "beauty": {
        "display": "뷰티·패션",
        "traits": {"ei": 0.8, "ns": -0.8, "tf": 0.8, "jp": 0.3, "adv": 0.3, "amb": 0.3},
        "fanLabel": "나를 가꾸는 걸 즐기는 트렌드세터",
        "why": "감각적으로 나를 표현하는 걸 아는 사람. 취향과 라이프스타일을 세련되게 채워줄 책들.",
        "kw": ["뷰티", "메이크업", "패션", "코디", "화장", "get ready", "grwm", "스타일"],
        "search": "뷰티 패션 유튜버",
        "bookQuery": "라이프스타일",
    },
    "music": {
        "display": "음악·커버",
        "traits": {"ei": 0.5, "ns": 0.8, "tf": 1.2, "jp": -0.3, "adv": 0.2, "amb": 0.2},
        "fanLabel": "선율에 감정을 싣는 낭만가",
        "why": "노래 한 곡에 하루의 온도가 바뀌는 사람. 감성과 여운이 오래 남는 이야기들이 어울려요.",
        "kw": ["음악", "커버", "노래", "보컬", "피아노", "밴드", "music", "cover", "버스킹"],
        "search": "음악 커버 유튜버",
        "bookQuery": "감성 소설",
    },
    "sports": {
        "display": "스포츠·운동",
        "traits": {"ei": 0.8, "ns": -0.5, "tf": -0.5, "jp": 0.8, "adv": 0.8, "amb": 1.2},
        "fanLabel": "한계를 넘는 걸 즐기는 도전가",
        "why": "몸을 움직일 때 가장 나다운 사람. 성장과 도전, 꾸준함의 가치를 담은 책들이 당신을 자극할 거예요.",
        "kw": ["운동", "헬스", "홈트", "축구", "야구", "스포츠", "피트니스", "다이어트", "등산"],
        "search": "운동 헬스 유튜버",
        "bookQuery": "운동",
    },
    "tech": {
        "display": "IT·테크",
        "traits": {"ei": -0.3, "ns": 0.5, "tf": -1.3, "jp": 0.3, "adv": 0.5, "amb": 0.7},
        "fanLabel": "새로운 기술에 눈 반짝이는 얼리어답터",
        "why": "최신 가젯과 기술 트렌드에 먼저 반응하는 사람. 미래와 혁신을 다루는 통찰서가 어울려요.",
        "kw": ["it", "테크", "리뷰", "가젯", "스마트폰", "ai", "개발", "코딩", "언박싱", "tech"],
        "search": "IT 테크 리뷰 유튜버",
        "bookQuery": "미래 기술",
    },
}


def yget(endpoint, **params):
    params["key"] = YT_KEY
    r = requests.get(f"{YT}/{endpoint}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def collect_channels():
    """Return {channelId: category_key_or_None}."""
    labeled = {}

    print("- trending (KR mostPopular)")
    try:
        data = yget("videos", part="snippet", chart="mostPopular", regionCode="KR", maxResults=50)
        for it in data.get("items", []):
            labeled.setdefault(it["snippet"]["channelId"], None)
    except Exception as e:
        print("  trending failed:", e)

    for key, cfg in CATEGORIES.items():
        print(f"- search: {cfg['search']}")
        try:
            data = yget(
                "search", part="snippet", q=cfg["search"], type="channel",
                maxResults=20, regionCode="KR", relevanceLanguage="ko",
            )
            for it in data.get("items", []):
                cid = it["snippet"]["channelId"]
                if labeled.get(cid) is None:
                    labeled[cid] = key
        except Exception as e:
            print("  search failed:", e)
        time.sleep(0.1)
    return labeled


def fetch_stats(channel_ids):
    out = {}
    for i in range(0, len(channel_ids), 50):
        chunk = channel_ids[i : i + 50]
        data = yget("channels", part="snippet,statistics", id=",".join(chunk))
        for it in data.get("items", []):
            st = it.get("statistics", {})
            thumbs = it["snippet"].get("thumbnails", {})
            best = thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}
            out[it["id"]] = {
                "title": it["snippet"]["title"],
                "description": it["snippet"].get("description", ""),
                "subscribers": int(st.get("subscriberCount", 0)) if not st.get("hiddenSubscriberCount") else 0,
                "profileImage": best.get("url", ""),
            }
    return out


def classify(title, desc, current):
    if current:
        return current
    text = (title + " " + desc).lower()
    best, score = None, 0
    for key, cfg in CATEGORIES.items():
        s = sum(1 for kw in cfg["kw"] if kw.lower() in text)
        if s > score:
            best, score = key, s
    return best  # may be None if nothing matched


def build_book_pools():
    pools = {}
    for key, cfg in CATEGORIES.items():
        params = {
            "ttbkey": ALADIN_KEY, "Query": cfg["bookQuery"], "QueryType": "Keyword",
            "SearchTarget": "Book", "MaxResults": POOL_SIZE, "start": 1,
            "output": "JS", "Version": "20131101", "Cover": "Big", "Sort": "SalesPoint",
        }
        try:
            items = requests.get(ALADIN_URL, params=params, timeout=10).json().get("item", [])
        except Exception as e:
            print(f"  pool {key} failed:", e)
            items = []
        books = []
        for it in items:
            if not it.get("title") or not it.get("cover"):
                continue
            books.append({
                "book": it["title"].split(" - ")[0].strip(),
                "author": it.get("author", ""),
                "publisher": it.get("publisher", ""),
                "blurb": (it.get("description") or "").strip(),
                "cover": it.get("cover", ""),
                "buyLink": it.get("link", ""),
                "pubDate": it.get("pubDate", ""),
                "priceStandard": it.get("priceStandard", 0),
                "priceSales": it.get("priceSales", 0),
                "categoryName": it.get("categoryName", ""),
                "customerReviewRank": it.get("customerReviewRank", 0),
            })
        pools[key] = books
        print(f"  pool {key}: {len(books)} books")
        time.sleep(0.2)
    return pools


def _hash_int(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def offset_traits(base, channel_id):
    h = _hash_int(channel_id)
    out = dict(base)
    # nudge two axes deterministically within [-0.4, 0.4]
    for i, ax in enumerate(AXES):
        bit = (h >> (i * 5)) & 0x1F
        out[ax] = round(out.get(ax, 0.0) + (bit / 31.0 - 0.5) * 0.8, 3)
    return out


def pick_books(pool, channel_id):
    if not pool:
        return []
    start = _hash_int(channel_id) % len(pool)
    return [pool[(start + k) % len(pool)] for k in range(min(BOOKS_PER_PERSONA, len(pool)))]


def main():
    if not YT_KEY or not ALADIN_KEY:
        print("ERROR: need YOUTUBE_API_KEY and ALADIN_TTB_KEY in .env")
        return

    labeled = collect_channels()
    print(f"collected {len(labeled)} channel ids")

    stats = fetch_stats(list(labeled.keys()))
    pools = build_book_pools()

    personas = []
    for cid, cat in labeled.items():
        info = stats.get(cid)
        if not info or info["subscribers"] < MIN_SUBS:
            continue
        key = classify(info["title"], info["description"], cat)
        if not key or not pools.get(key):
            continue  # skip if unclassifiable or its book pool came back empty
        cfg = CATEGORIES[key]
        personas.append({
            "id": cid,
            "youtuber": info["title"],
            "profileImage": info["profileImage"],
            "channelUrl": f"https://www.youtube.com/channel/{cid}",
            "subscribers": info["subscribers"],
            "category": cfg["display"],
            "fanLabel": cfg["fanLabel"],
            "why": cfg["why"],
            "traits": offset_traits(cfg["traits"], cid),
            "books": pick_books(pools[key], cid),
        })

    personas.sort(key=lambda p: p["subscribers"], reverse=True)

    data = {
        "axes": {
            "ei": "외향(+)/내향(-)", "ns": "직관·상상(+)/감각·현실(-)",
            "tf": "감정·공감(+)/사고·논리(-)", "jp": "계획·체계(+)/즉흥·유연(-)",
            "adv": "모험·새로움(+)/안정·집콕(-)", "amb": "성장·야망(+)/여유·즐김(-)",
        },
        "personas": personas,
    }
    PERSONAS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    dist = Counter(p["category"] for p in personas)
    print(f"\nWrote {len(personas)} personas")
    for c, n in dist.most_common():
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
