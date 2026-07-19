"""Hacker News connector (`docs/03-SOURCING.md` §2.2) — launch traction
and technical-audience engagement via the Algolia HN Search API (no auth,
generous rate limits). Cached in Bronze via `ingest_raw`.

Zero hits is a valid, common outcome (most seed-stage companies have no
HN presence yet) — never treated as a negative signal, only "no signal
from this channel" (`docs/00-OVERVIEW.md` §4 rule 3/6).
"""

from __future__ import annotations

from typing import Any

import httpx

from api.ingestion.memory import ingest_raw

HN_SEARCH_API = "https://hn.algolia.com/api/v1/search"


def fetch_launch_signals(query: str) -> dict[str, Any] | None:
    try:
        resp = httpx.get(
            HN_SEARCH_API,
            params={"query": query, "tags": "story", "hitsPerPage": 10},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 — connector failures degrade to "no signal", never crash
        print(f"[hackernews] search failed for {query!r}: {exc}")
        return None

    hits = data.get("hits", [])
    if not hits:
        return None

    total_points = sum(h.get("points") or 0 for h in hits)
    total_comments = sum(h.get("num_comments") or 0 for h in hits)
    top_hit = max(hits, key=lambda h: h.get("points") or 0)

    signals = {
        "query": query,
        "story_count": len(hits),
        "total_points": total_points,
        "total_comments": total_comments,
        "top_story_title": top_hit.get("title"),
        "top_story_points": top_hit.get("points"),
        "top_story_url": top_hit.get("url") or f"https://news.ycombinator.com/item?id={top_hit.get('objectID')}",
        "most_recent_at": max((h.get("created_at") for h in hits if h.get("created_at")), default=None),
    }

    ingest_raw("hackernews", signals, entity_type="story_search", source_entity_id=query)
    return signals
