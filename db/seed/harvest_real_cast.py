#!/usr/bin/env python3
"""Harvest public footprints for a curated founder cast into
`shared/fixtures/real-cast.json`.

Sources (public only): LinkedIn via Tavily site: search, Perplexity research,
GitHub REST, Hacker News Algolia, arXiv Atom API. Never invents traction —
missing channels stay null / empty.

Usage (from repo root, with API keys in .env):

    python db/seed/harvest_real_cast.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
load_dotenv(REPO_ROOT / ".env")

from api.agent import perplexity  # noqa: E402
from api.ingestion.connectors import arxiv, github, hackernews, linkedin  # noqa: E402
from api.intelligence import retrieval  # noqa: E402

OUT_PATH = REPO_ROOT / "shared" / "fixtures" / "real-cast.json"

# Curated cast from investor-supplied LinkedIn URLs (2026-07-18).
CAST = [
    {"slug": "founder-amit-shah", "linkedin_slug": "amitshahny", "hint_name": "Amit Shah"},
    {"slug": "founder-ana-montero", "linkedin_slug": "anamonterohoras", "hint_name": "Ana Montero"},
    {"slug": "founder-seb-peralta", "linkedin_slug": "sebjperalta", "hint_name": "Sebastian Peralta"},
    {"slug": "founder-dylan-ma", "linkedin_slug": "dylanma5621", "hint_name": "Dylan Ma"},
    {"slug": "founder-ardalan-jam", "linkedin_slug": "ardalanjam1369", "hint_name": "Ardalan Jam"},
    {"slug": "founder-andi-partovi", "linkedin_slug": "andi-partovi", "hint_name": "Andi Partovi"},
]

_GITHUB_RE = re.compile(r"github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)
_GH_BLOCK = {"features", "about", "pricing", "topics", "sponsors", "orgs", "marketplace", "collections", "settings"}


def _extract_github(text: str) -> str | None:
    for m in _GITHUB_RE.finditer(text or ""):
        login = m.group(1)
        if login.lower() not in _GH_BLOCK:
            return login
    return None


def _company_guess(answer: str, headline: str | None) -> str | None:
    # Prefer "founder of X" / "CEO of X" patterns; never invent.
    blob = f"{headline or ''} {answer or ''}"
    for pat in (
        r"(?:founder|co-?founder|CEO|CTO)\s+(?:of|at)\s+([A-Z][\w.&' -]{1,40})",
        r"at\s+([A-Z][\w.&' -]{1,40})\s+(?:as|,)",
    ):
        m = re.search(pat, blob)
        if m:
            name = m.group(1).strip(" .,;")
            if len(name) >= 2 and name.lower() not in {"the", "a", "an", "linkedin"}:
                return name
    return None


def harvest_one(entry: dict[str, str]) -> dict[str, Any]:
    li_url = f"https://www.linkedin.com/in/{entry['linkedin_slug']}"
    hint = entry["hint_name"]
    print(f"\n=== {hint} ({li_url}) ===")

    li = linkedin.fetch_profile_signals(hint, linkedin_url=li_url)
    headline = (li or {}).get("headline")
    snippet = (li or {}).get("snippet")
    print(f"  linkedin: {'hit' if li else 'miss'} — {(headline or '')[:80]}")

    research_q = (
        f"Who is {hint}? LinkedIn: {li_url}. "
        f"Current role, company, GitHub username if public, any arXiv papers, "
        f"Hacker News or Show HN mentions. Cite sources. Do not invent funding or ARR."
    )
    pplx = perplexity.research(research_q)
    answer = (pplx or {}).get("answer") or ""
    citations = (pplx or {}).get("citations") or []
    print(f"  perplexity: {'hit' if pplx else 'miss'} — {len(answer)} chars, {len(citations)} cites")

    blob = " ".join(
        [
            hint,
            headline or "",
            snippet or "",
            answer,
            " ".join(citations),
        ]
    )
    gh_login = _extract_github(blob)
    if not gh_login and retrieval.is_available():
        # Secondary: web search for github.com/<login>
        hits = retrieval.search(f'{hint} github.com', max_results=5)
        for h in hits:
            gh_login = _extract_github((h.get("url") or "") + " " + (h.get("content") or ""))
            if gh_login:
                break
    gh = github.fetch_profile_signals(gh_login) if gh_login else None
    print(f"  github: {gh_login or 'none'} — {'hit' if gh else 'miss'}")

    company_name = _company_guess(answer, headline)
    hn_q = company_name or hint
    hn = hackernews.fetch_launch_signals(hn_q)
    print(f"  hackernews ({hn_q!r}): {'hit' if hn else 'miss'}")

    ax = arxiv.fetch_paper_signals(hint)
    print(f"  arxiv: {'hit' if ax else 'miss'}")

    display_name = hint
    if gh and gh.get("bio"):
        # Prefer LinkedIn/Perplexity name; GitHub name if present in research
        pass
    # Try to refine name from Perplexity first line
    m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z'\-]+)+)", answer.strip())
    if m and hint.split()[0].lower() in m.group(1).lower():
        display_name = m.group(1)

    return {
        "slug": entry["slug"],
        "display_name": display_name,
        "linkedin_url": li_url,
        "linkedin_slug": entry["linkedin_slug"],
        "company_name": company_name,
        "github_username": gh_login,
        "signals": {
            "linkedin": li,
            "perplexity": {
                "answer": answer[:2000] if answer else None,
                "citations": citations[:8],
            } if pplx else None,
            "github": gh,
            "hackernews": hn,
            "arxiv": ax,
        },
        "harvested_at": datetime.now(timezone.utc).isoformat(),
        "access_modes": {
            "linkedin": "public_web_search",
            "github": "public_rest_api",
            "hackernews": "algolia_public",
            "arxiv": "atom_public",
            "perplexity": "search_grounded_research",
        },
        "notes": "Public signals only. Traction/ARR not asserted unless cited in perplexity/github/hn.",
    }


def build_network(people: list[dict[str, Any]]) -> dict[str, Any]:
    """Small real-ish network: founder↔company + shared anchors + peer edges
    between cast members who share a channel (HN/github/arxiv presence)."""
    nodes: list[dict[str, Any]] = [
        {"slug": "anchor-yc", "type": "Accelerator", "label": "Y Combinator", "confidence": 0.95, "tags": ["anchor"]},
        {"slug": "anchor-a16z", "type": "VC", "label": "Andreessen Horowitz", "confidence": 0.9, "tags": ["anchor", "tier1_vc"]},
        {"slug": "anchor-github", "type": "Institution", "label": "GitHub OSS community", "confidence": 0.7, "tags": ["anchor"]},
        {"slug": "anchor-arxiv", "type": "Institution", "label": "arXiv", "confidence": 0.85, "tags": ["anchor"]},
    ]
    edges: list[dict[str, Any]] = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for p in people:
        nodes.append({
            "slug": p["slug"],
            "type": "Founder",
            "label": p["display_name"],
            "confidence": 0.8,
            "tags": ["real_cast"],
            "linkedin_url": p["linkedin_url"],
            "github_username": p.get("github_username"),
        })
        if p.get("company_name"):
            cslug = "company-" + re.sub(r"[^a-z0-9]+", "-", p["company_name"].lower()).strip("-")[:40]
            nodes.append({
                "slug": cslug,
                "type": "Company",
                "label": p["company_name"],
                "confidence": 0.6,
                "tags": ["real_cast"],
            })
            edges.append({
                "from": p["slug"],
                "to": cslug,
                "relation_type": "CO_CONTRIBUTED",
                "weight": 0.85,
                "first_seen_at": today,
                "evidence": "role inferred from public research / LinkedIn snippet",
            })
        if p.get("github_username") and p["signals"].get("github"):
            edges.append({
                "from": p["slug"],
                "to": "anchor-github",
                "relation_type": "CO_CONTRIBUTED",
                "weight": min(0.9, 0.4 + (p["signals"]["github"].get("total_stars") or 0) / 500),
                "first_seen_at": today,
                "evidence": f"github:{p['github_username']}",
            })
        if p["signals"].get("arxiv"):
            edges.append({
                "from": p["slug"],
                "to": "anchor-arxiv",
                "relation_type": "CO_AUTHORED",
                "weight": 0.7,
                "first_seen_at": today,
                "evidence": "arxiv paper hit",
            })
        if p["signals"].get("hackernews"):
            edges.append({
                "from": p["slug"],
                "to": "anchor-yc",  # HN ≠ YC, but launch community proximity for demo graph
                "relation_type": "CO_PARTICIPATED",
                "weight": 0.45,
                "first_seen_at": today,
                "evidence": "hackernews launch/community signal",
            })

    # Peer edges: co-presence in cast (hackathon / shared sourcing batch)
    for i, a in enumerate(people):
        for b in people[i + 1 :]:
            edges.append({
                "from": a["slug"],
                "to": b["slug"],
                "relation_type": "CO_PARTICIPATED",
                "weight": 0.35,
                "first_seen_at": today,
                "evidence": "same sourcing cohort (Hack Nation real-cast harvest)",
            })

    # Dedupe nodes by slug
    by_slug = {n["slug"]: n for n in nodes}
    return {"nodes": list(by_slug.values()), "edges": edges}


def main() -> None:
    print("Harvesting real cast (public signals only)...")
    if not perplexity.is_available():
        print("WARN: PERPLEXITY_API_KEY missing — research will be thin")
    if not retrieval.is_available():
        print("WARN: TAVILY_API_KEY missing — LinkedIn/web search will miss")

    people = []
    for entry in CAST:
        try:
            people.append(harvest_one(entry))
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED {entry['slug']}: {exc}")
            people.append({
                **entry,
                "display_name": entry["hint_name"],
                "linkedin_url": f"https://www.linkedin.com/in/{entry['linkedin_slug']}",
                "error": str(exc),
                "signals": {},
            })
        time.sleep(0.4)  # be polite to APIs

    payload = {
        "version": 1,
        "harvested_at": datetime.now(timezone.utc).isoformat(),
        "source": "investor-supplied LinkedIn URLs",
        "people": people,
        "network": build_network([p for p in people if not p.get("error")]),
        "disclaimer": (
            "Public-web footprints only. Not LinkedIn partner API. "
            "Do not treat research text as verified traction. Gap-flag unknowns in memos."
        ),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}")
    print(f"People: {len(people)} · network nodes: {len(payload['network']['nodes'])} · edges: {len(payload['network']['edges'])}")


if __name__ == "__main__":
    main()
