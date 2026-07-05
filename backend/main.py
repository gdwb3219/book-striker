import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

# Load .env before importing modules that read env at import time.
load_dotenv(Path(__file__).parent / ".env")

import matching

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "stats.db"
CONTENT_PATH = BASE_DIR / "content.json"
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.on_event("startup")
def init_db() -> None:
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            referrer TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def record_event(event_type: str, referrer: str | None) -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO stats (event_type, referrer, created_at) VALUES (?, ?, ?)",
        (event_type, referrer, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/content")
def get_content():
    with open(CONTENT_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/match")
async def post_match(request: Request):
    body = await request.json()
    vector = body.get("vector", {})
    if not isinstance(vector, dict):
        raise HTTPException(status_code=400, detail="vector must be an object")
    return matching.match(vector)


@app.post("/api/view")
def post_view(request: Request):
    record_event("view", request.headers.get("referer"))
    return {"ok": True}


@app.post("/api/share")
def post_share(request: Request):
    record_event("share", request.headers.get("referer"))
    return {"ok": True}


@app.get("/api/stats")
def get_stats():
    conn = get_db()
    views = conn.execute(
        "SELECT COUNT(*) AS c FROM stats WHERE event_type = 'view'"
    ).fetchone()["c"]
    shares = conn.execute(
        "SELECT COUNT(*) AS c FROM stats WHERE event_type = 'share'"
    ).fetchone()["c"]
    top_referrers = conn.execute(
        """
        SELECT referrer, COUNT(*) AS c FROM stats
        WHERE referrer IS NOT NULL
        GROUP BY referrer ORDER BY c DESC LIMIT 10
        """
    ).fetchall()
    conn.close()
    return {
        "views": views,
        "shares": shares,
        "top_referrers": [dict(r) for r in top_referrers],
    }
