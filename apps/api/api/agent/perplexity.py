"""Perplexity client — search-grounded research with native citations
(`docs/05-CURSOR-SKILLS.md` §2). Retries transient failures, caches
identical queries in-memory for a short TTL (repeated sourcing sweeps and
demo re-runs shouldn't re-pay for the same search), and extracts
`search_results` into `EvidenceRef`-shaped dicts.

No key, or failure after retries, returns `None` — callers degrade to
"no research available" rather than crashing or fabricating leads.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from api.core.config import settings

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar"
CACHE_TTL_SECONDS = 60 * 60  # 1 hour — sourcing sweeps re-run often during a demo

_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def is_available() -> bool:
    return bool(settings.perplexity_api_key)


def _cache_get(key: str) -> dict[str, Any] | None:
    hit = _cache.get(key)
    if hit is None:
        return None
    cached_at, value = hit
    if time.time() - cached_at > CACHE_TTL_SECONDS:
        del _cache[key]
        return None
    return value


def research(query: str, *, retries: int = 2) -> dict[str, Any] | None:
    """Returns `{"answer": str, "evidence": [EvidenceRef], "citations": [url]}`
    or `None` if no key or every attempt failed."""
    if not is_available():
        return None

    cached = _cache_get(query)
    if cached is not None:
        return cached

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = httpx.post(
                PERPLEXITY_URL,
                headers={"Authorization": f"Bearer {settings.perplexity_api_key}", "Content-Type": "application/json"},
                json={"model": MODEL, "messages": [{"role": "user", "content": query}]},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            evidence = [
                {
                    "source_type": "web",
                    "source_locator": r.get("url", ""),
                    "evidence_snippet": (r.get("snippet") or "")[:400],
                    "confidence": 0.6,
                    "title": r.get("title"),
                }
                for r in (data.get("search_results") or [])[:8]
            ]
            result = {"answer": answer, "evidence": evidence, "citations": data.get("citations", [])}
            _cache[query] = (time.time(), result)
            return result
        except Exception as exc:  # noqa: BLE001 — must degrade to "no research", never crash the sweep
            last_exc = exc
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
            continue

    print(f"[perplexity] research failed after {retries + 1} attempt(s) for {query!r}: {last_exc}")
    return None
