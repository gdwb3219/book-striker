"""Match a user trait vector to the nearest YouTuber fan persona."""

import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).parent
PERSONAS_PATH = BASE_DIR / "personas.json"

AXES = ["ei", "ns", "tf", "jp", "adv", "amb"]

_data = json.loads(PERSONAS_PATH.read_text(encoding="utf-8"))
PERSONAS = _data["personas"]
AXES_INFO = _data.get("axes", {})


def _distance(a: dict, b: dict) -> float:
    return math.sqrt(sum((a.get(ax, 0.0) - b.get(ax, 0.0)) ** 2 for ax in AXES))


def _public_persona(persona: dict, distance: float) -> dict:
    books = [
        {k: v for k, v in book.items() if k != "query"} for book in persona["books"]
    ]
    return {
        "id": persona["id"],
        "youtuber": persona["youtuber"],
        "profileImage": persona.get("profileImage", ""),
        "channelUrl": persona["channelUrl"],
        "subscribers": persona["subscribers"],
        "category": persona["category"],
        "fanLabel": persona["fanLabel"],
        "why": persona["why"],
        "distance": round(distance, 3),
        "books": books,
    }


def match(user_vector: dict) -> dict:
    vec = {ax: float(user_vector.get(ax, 0.0)) for ax in AXES}
    ranked = sorted(PERSONAS, key=lambda p: _distance(vec, p["traits"]))
    best = ranked[0]
    runners = [
        {
            "id": p["id"],
            "youtuber": p["youtuber"],
            "category": p["category"],
            "fanLabel": p["fanLabel"],
        }
        for p in ranked[1:3]
    ]
    return {
        "vector": {ax: round(vec[ax], 2) for ax in AXES},
        "match": _public_persona(best, _distance(vec, best["traits"])),
        "runnersUp": runners,
    }
