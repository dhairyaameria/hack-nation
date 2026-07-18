"""Tavily search wrapper — the Validator's external corroboration source
(`docs/04-INTELLIGENCE-TRUST.md` §2 item 2).

No key, or any request failure, returns an empty result list — an empty
list is exactly what makes a claim `unknown` rather than fabricated as
`verified`/`contradicted` (see `docs/00-OVERVIEW.md` §4 rule 3/6).
"""

from __future__ import annotations

import httpx

from api.core.config import settings

TAVILY_URL = "https://api.tavily.com/search"


def is_available() -> bool:
    return bool(settings.tavily_api_key)


def search(query: str, max_results: int = 3) -> list[dict]:
    if not is_available():
        return []
    try:
        resp = httpx.post(
            TAVILY_URL,
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": (r.get("content") or "")[:500],
            }
            for r in results
        ]
    except Exception as exc:  # noqa: BLE001 — network/API failures must degrade to "no evidence found"
        print(f"[retrieval] Tavily search failed for {query!r}: {exc}")
        return []
