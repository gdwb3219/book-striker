"""Resolve curated Korean YouTuber anchors -> real channel stats via API."""

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
YT_KEY = os.environ.get("YOUTUBE_API_KEY")
YT = "https://www.googleapis.com/youtube/v3"

# domain -> search term (well-known Korean channels)
ANCHORS = {
    "economy_society": "슈카월드",
    "travel_adventure": "빠니보틀",
    "self_growth": "드로우앤드류",
    "knowledge_science": "안될과학",
    "comedy_entertain": "피식대학",
    "game_community": "우왁굳",
    "food_mukbang": "쯔양",
    "healing_vlog": "슛뚜",
}


def _get(endpoint, **params):
    params["key"] = YT_KEY
    r = requests.get(f"{YT}/{endpoint}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def resolve(term):
    data = _get("search", part="snippet", q=term, type="channel", maxResults=1)
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["snippet"]["channelId"]


def main():
    out = []
    for domain, term in ANCHORS.items():
        cid = resolve(term)
        if not cid:
            out.append({"domain": domain, "term": term, "error": "not found"})
            continue
        data = _get("channels", part="snippet,statistics", id=cid)
        item = data["items"][0]
        stats = item["statistics"]
        out.append(
            {
                "domain": domain,
                "term": term,
                "channelId": cid,
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", "")[:120],
                "subscribers": int(stats.get("subscriberCount", 0)),
                "videoCount": int(stats.get("videoCount", 0)),
            }
        )
    p = BASE_DIR / "anchors.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    # also a readable txt
    lines = [
        f"{a.get('subscribers',0):>12,}  [{a['domain']}]  {a.get('title','?')}  ::  {a.get('description','')}"
        for a in out
    ]
    (BASE_DIR / "anchors.txt").write_text("\n".join(lines), encoding="utf-8")
    print("done", len(out))


if __name__ == "__main__":
    main()
