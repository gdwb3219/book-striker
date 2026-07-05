"""Build step: fill persona book entries with real Aladin metadata and each
persona's YouTube channel profile image.

Run: python enrich_books.py
Requires ALADIN_TTB_KEY (+ YOUTUBE_API_KEY for profile images) in .env.
Failures leave fields empty, so runtime never depends on either API.
"""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

ALADIN_TTB_KEY = os.environ.get("ALADIN_TTB_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
ALADIN_API_URL = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
YT_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
PERSONAS_PATH = BASE_DIR / "personas.json"


def lookup(query: str) -> dict:
    params = {
        "ttbkey": ALADIN_TTB_KEY,
        "Query": query,
        "QueryType": "Keyword",
        "SearchTarget": "Book",
        "MaxResults": 1,
        "start": 1,
        "output": "JS",
        "Version": "20131101",
        "Cover": "Big",
    }
    res = requests.get(ALADIN_API_URL, params=params, timeout=8)
    res.raise_for_status()
    items = res.json().get("item", [])
    if not items:
        return {}
    it = items[0]
    return {
        "book": it.get("title", "").split(" - ")[0].strip() or query,
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
    }


def fetch_profile_image(channel_url: str) -> str:
    if not YOUTUBE_API_KEY:
        return ""
    channel_id = channel_url.rstrip("/").split("/")[-1]
    try:
        res = requests.get(
            YT_CHANNELS_URL,
            params={"part": "snippet", "id": channel_id, "key": YOUTUBE_API_KEY},
            timeout=8,
        )
        res.raise_for_status()
        items = res.json().get("items", [])
        if not items:
            return ""
        thumbs = items[0]["snippet"].get("thumbnails", {})
        best = thumbs.get("high") or thumbs.get("medium") or thumbs.get("default")
        return best.get("url", "") if best else ""
    except Exception:
        return ""


def main():
    if not ALADIN_TTB_KEY:
        print("ERROR: ALADIN_TTB_KEY not set")
        return

    data = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
    for persona in data["personas"]:
        persona["profileImage"] = fetch_profile_image(persona["channelUrl"])
        print(f"[{persona['youtuber']}] profile={'Y' if persona['profileImage'] else 'N'}")
        for book in persona["books"]:
            q = book["query"]
            try:
                info = lookup(q)
            except Exception as e:
                print(f"  ! {q}: {e}")
                info = {}
            if info:
                # keep curated title/author, fill the rest from Aladin
                book["publisher"] = info.get("publisher", book.get("publisher", ""))
                book["cover"] = info.get("cover", "")
                book["buyLink"] = info.get("buyLink", "")
                book["pubDate"] = info.get("pubDate", "")
                book["priceStandard"] = info.get("priceStandard", 0)
                book["priceSales"] = info.get("priceSales", 0)
                book["categoryName"] = info.get("categoryName", "")
                book["customerReviewRank"] = info.get("customerReviewRank", 0)
                if not book.get("blurb"):
                    book["blurb"] = info.get("blurb", "")
                print(f"  OK {book['book']} -> {info.get('pubDate','?')} / {info.get('priceStandard',0)}원")
            else:
                for k, d in (
                    ("publisher", ""), ("cover", ""), ("buyLink", ""), ("blurb", ""),
                    ("pubDate", ""), ("priceStandard", 0), ("priceSales", 0),
                    ("categoryName", ""), ("customerReviewRank", 0),
                ):
                    book.setdefault(k, d)
                print(f"  -- {q}: no result")
            time.sleep(0.2)

    PERSONAS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\nWrote", PERSONAS_PATH)


if __name__ == "__main__":
    main()
