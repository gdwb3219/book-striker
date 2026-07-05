"""Offline pipeline: fetch trending/popular Korean YouTube channels + sample
comments, dump raw data to personas_raw.json for analysis.

Run: python build_personas.py fetch
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

YT_KEY = os.environ.get("YOUTUBE_API_KEY")
YT = "https://www.googleapis.com/youtube/v3"
RAW_PATH = BASE_DIR / "personas_raw.json"


def _get(endpoint: str, **params) -> dict:
    params["key"] = YT_KEY
    r = requests.get(f"{YT}/{endpoint}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_trending_channels(region="KR", max_videos=50) -> list[str]:
    data = _get(
        "videos",
        part="snippet",
        chart="mostPopular",
        regionCode=region,
        maxResults=max_videos,
    )
    seen, ids = set(), []
    for item in data.get("items", []):
        cid = item["snippet"]["channelId"]
        if cid not in seen:
            seen.add(cid)
            ids.append(cid)
    return ids


def fetch_channel_stats(channel_ids: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(channel_ids), 50):
        chunk = channel_ids[i : i + 50]
        data = _get(
            "channels",
            part="snippet,statistics",
            id=",".join(chunk),
        )
        for item in data.get("items", []):
            stats = item.get("statistics", {})
            out.append(
                {
                    "channelId": item["id"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"].get("description", ""),
                    "subscribers": int(stats.get("subscriberCount", 0)),
                    "videoCount": int(stats.get("videoCount", 0)),
                    "viewCount": int(stats.get("viewCount", 0)),
                }
            )
    return out


def fetch_top_comments(channel_id: str, limit=15) -> list[str]:
    try:
        data = _get(
            "commentThreads",
            part="snippet",
            allThreadsRelatedToChannelId=channel_id,
            order="relevance",
            maxResults=limit,
            textFormat="plainText",
        )
    except Exception:
        return []
    comments = []
    for item in data.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]
        comments.append(top.get("textDisplay", "").strip())
    return [c for c in comments if c]


def main():
    if not YT_KEY:
        print("ERROR: YOUTUBE_API_KEY not set in .env")
        sys.exit(1)

    print("1) trending channels (KR mostPopular)...")
    ids = fetch_trending_channels()
    print(f"   {len(ids)} unique channels")

    print("2) channel stats...")
    channels = fetch_channel_stats(ids)
    channels.sort(key=lambda c: c["subscribers"], reverse=True)

    print("3) top comments (top 20 channels by subs)...")
    for ch in channels[:20]:
        ch["sample_comments"] = fetch_top_comments(ch["channelId"])
        print(f"   {ch['title']} ({ch['subscribers']:,}) - {len(ch['sample_comments'])} comments")

    RAW_PATH.write_text(
        json.dumps(channels, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {RAW_PATH} ({len(channels)} channels)")


if __name__ == "__main__":
    main()
