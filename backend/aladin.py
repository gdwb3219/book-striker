import json
import os
import random
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
FALLBACK_PATH = BASE_DIR / "fallback_results.json"

ALADIN_TTB_KEY = os.environ.get("ALADIN_TTB_KEY")
ALADIN_API_URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6h — keeps recommendations fresh without hammering the API on every request

TAG_QUERIES = {
    "healing": "에세이 힐링",
    "growth": "성장 소설",
    "thriller": "스릴러 소설",
    "fantasy": "판타지 소설",
    "selfhelp": "자기계발",
}

_cache: dict[str, tuple[float, list[dict]]] = {}


def _load_fallback(tag: str) -> dict:
    with open(FALLBACK_PATH, encoding="utf-8") as f:
        fallback = json.load(f)
    return fallback[tag]


def _fetch_candidates(tag: str) -> list[dict]:
    query = TAG_QUERIES[tag]
    params = {
        "ttbkey": ALADIN_TTB_KEY,
        "Query": query,
        "QueryType": "Keyword",
        "SearchTarget": "Book",
        "MaxResults": 10,
        "start": 1,
        "output": "JS",
        "Version": "20131101",
        "Cover": "Big",
    }
    res = requests.get(ALADIN_API_URL, params=params, timeout=5)
    res.raise_for_status()
    data = res.json()
    items = data.get("item", [])
    return [
        {
            "book": item["title"],
            "author": item["author"],
            "publisher": item["publisher"],
            "blurb": (item.get("description") or "").strip() or f"{query} 분야 추천작.",
            "buyLink": item["link"],
        }
        for item in items
        if item.get("title") and item.get("link")
    ]


def get_book_for_tag(tag: str) -> dict:
    if not ALADIN_TTB_KEY:
        return _load_fallback(tag)

    now = time.time()
    cached = _cache.get(tag)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        candidates = cached[1]
    else:
        try:
            candidates = _fetch_candidates(tag)
            if not candidates:
                raise ValueError("empty result from Aladin API")
            _cache[tag] = (now, candidates)
        except Exception:
            return _load_fallback(tag)

    return random.choice(candidates)
