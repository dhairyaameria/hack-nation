"""arXiv connector — papers / academic footprint signals for technical
founders (`docs/03-SOURCING.md` §2). Uses the public Atom API; no key.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote_plus

import httpx

from api.ingestion.memory import ingest_raw

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"


def fetch_paper_signals(query: str, *, max_results: int = 5) -> dict[str, Any] | None:
    """Search arXiv for papers matching a founder/company query."""
    if not query.strip():
        return None
    try:
        resp = httpx.get(
            ARXIV_API,
            params={
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
            timeout=20,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        entries = root.findall(f"{ATOM}entry")
        if not entries:
            return None

        papers = []
        for entry in entries:
            title = (entry.findtext(f"{ATOM}title") or "").strip().replace("\n", " ")
            published = (entry.findtext(f"{ATOM}published") or "")[:10]
            link_el = entry.find(f"{ATOM}id")
            link = (link_el.text or "").strip() if link_el is not None else ""
            authors = [
                (a.findtext(f"{ATOM}name") or "").strip()
                for a in entry.findall(f"{ATOM}author")
            ]
            papers.append({
                "title": title,
                "published": published,
                "url": link,
                "authors": authors,
            })

        signals = {
            "channel": "arxiv",
            "query": query,
            "paper_count": len(papers),
            "top_title": papers[0]["title"] if papers else None,
            "top_url": papers[0]["url"] if papers else None,
            "papers": papers,
        }
        ingest_raw("arxiv", signals, entity_type="paper_search", source_entity_id=query)
        return signals
    except Exception as exc:  # noqa: BLE001
        print(f"[arxiv] search failed for {query!r}: {exc}")
        return None
