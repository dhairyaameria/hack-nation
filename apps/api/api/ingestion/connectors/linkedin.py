"""LinkedIn outbound signal connector (`docs/03-SOURCING.md` §2).

LinkedIn's official Profile API is partner-gated and unavailable for a
hackathon stack. This connector uses Tavily restricted to
`site:linkedin.com/in` (or a caller-supplied profile URL) to surface
public LinkedIn footprint evidence into Bronze — same provenance rules
as every other connector. Absence of a hit is "no signal", never a
negative score.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from api.ingestion.memory import ingest_raw
from api.intelligence import retrieval

_LINKEDIN_IN_RE = re.compile(
    r"https?://(?:[\w.-]+\.)?linkedin\.com/in/([A-Za-z0-9_-]+)/?",
    re.IGNORECASE,
)


def normalize_profile_url(value: str | None) -> str | None:
    """Accept a full LinkedIn URL or a bare vanity slug → canonical /in/ URL."""
    if not value or not value.strip():
        return None
    raw = value.strip()
    m = _LINKEDIN_IN_RE.search(raw)
    if m:
        return f"https://www.linkedin.com/in/{m.group(1)}"
    # Bare slug (no spaces, no protocol)
    if re.fullmatch(r"[A-Za-z0-9_-]{2,100}", raw) and "://" not in raw:
        return f"https://www.linkedin.com/in/{raw}"
    # Path-only /in/foo
    if raw.startswith("/in/"):
        slug = raw.split("/in/", 1)[1].strip("/").split("/")[0]
        if slug:
            return f"https://www.linkedin.com/in/{slug}"
    return None


def extract_profile_url_from_text(text: str) -> str | None:
    m = _LINKEDIN_IN_RE.search(text or "")
    return f"https://www.linkedin.com/in/{m.group(1)}" if m else None


def fetch_profile_signals(
    founder_name: str,
    *,
    company_name: str | None = None,
    linkedin_url: str | None = None,
) -> dict[str, Any] | None:
    """Search public LinkedIn profile evidence via Tavily. Returns None if
    no LinkedIn-shaped results — cold-start friendly."""
    profile_url = normalize_profile_url(linkedin_url)

    if profile_url:
        query = f"{profile_url} {founder_name}"
    else:
        company_bit = f' "{company_name}"' if company_name else ""
        query = f'site:linkedin.com/in "{founder_name}"{company_bit} founder OR CEO OR co-founder'

    if not retrieval.is_available():
        return None

    results = retrieval.search(query, max_results=5)
    # Keep only linkedin.com/in hits — generic web noise belongs in web_search.
    li_results = []
    for r in results:
        url = r.get("url") or ""
        host = urlparse(url).netloc.lower()
        if "linkedin.com" in host and "/in/" in url:
            li_results.append(r)
            if not profile_url:
                profile_url = normalize_profile_url(url)

    if not li_results and not profile_url:
        return None

    # Prefer results that mention the founder name when we have several.
    name_token = founder_name.split()[-1].lower() if founder_name else ""
    ranked = sorted(
        li_results,
        key=lambda r: (
            0 if name_token and name_token in ((r.get("title") or "") + (r.get("content") or "")).lower() else 1,
            0 if profile_url and profile_url.rstrip("/") in (r.get("url") or "") else 1,
        ),
    )

    top = ranked[0] if ranked else None
    slug = None
    if profile_url:
        m = _LINKEDIN_IN_RE.search(profile_url)
        slug = m.group(1) if m else None

    signals: dict[str, Any] = {
        "channel": "linkedin",
        "query": query,
        "profile_url": profile_url,
        "vanity_slug": slug,
        "headline": (top.get("title") if top else None) or None,
        "snippet": ((top.get("content") if top else None) or "")[:400] or None,
        "result_count": len(ranked),
        "results": [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": (r.get("content") or "")[:300],
            }
            for r in ranked[:4]
        ],
        # Provenance note for the UI / judges — not a private LinkedIn API.
        "access_mode": "public_web_search",
    }

    ingest_raw(
        "linkedin",
        signals,
        entity_type="founder_profile",
        source_entity_id=slug or founder_name,
    )
    return signals
