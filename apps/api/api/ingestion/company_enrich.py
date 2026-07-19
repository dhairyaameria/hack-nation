"""Company profile enrichment via Perplexity + Tavily (cited web research).

Not a licensed Crunchbase/PitchBook feed — public research with provenance URLs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.agent import perplexity
from api.core.db import get_client
from api.intelligence import retrieval


def enrich_company(company_name: str, *, domain: str | None = None) -> dict[str, Any]:
    """Return structured enrichment payload (always safe to store as jsonb)."""
    q = (
        f"Company profile for {company_name}"
        + (f" ({domain})" if domain else "")
        + ". Write a concise diligence brief using markdown headings (###) and "
        "bullet lists — avoid markdown tables. Cover: what they build, sector, stage, "
        "founding year if known, notable funding/investors if public, competitors, "
        "and website. Prefer Crunchbase, PitchBook, company site, and reputable news. "
        "Keep citation markers like [1] inline where claims need sources."
    )
    answer = ""
    citations: list[str] = []
    evidence: list[dict[str, Any]] = []

    research = perplexity.research(q)
    if research:
        answer = research.get("answer") or ""
        citations = list(research.get("citations") or [])[:12]
        evidence = list(research.get("evidence") or [])[:12]

    web_q = f"{company_name} startup funding sector site:crunchbase.com OR site:techcrunch.com"
    web = retrieval.search(web_q, max_results=5) if retrieval.is_available() else []
    web_results = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "snippet": (r.get("content") or "")[:320],
        }
        for r in (web or [])
        if r.get("url")
    ]
    for r in web_results:
        if r["url"] not in citations:
            citations.append(r["url"])

    return {
        "summary": answer,
        "citations": citations[:16],
        "web_results": web_results,
        "evidence": evidence,
        "sources": ["perplexity", "tavily"] if web_results else (["perplexity"] if answer else []),
        "enriched_at": datetime.now(timezone.utc).isoformat(),
        "access_mode": "public_web_research",
        "disclaimer": (
            "Enriched from public web research (Perplexity/Tavily). "
            "Not a licensed Crunchbase or PitchBook API feed."
        ),
    }


def persist_company_enrichment(company_id: str, enrichment: dict[str, Any]) -> None:
    client = get_client()
    if client is None:
        return
    client.table("companies").update({
        "enrichment": enrichment,
        "enrichment_at": enrichment.get("enriched_at"),
        "description": (enrichment.get("summary") or "")[:2000] or None,
    }).eq("id", company_id).execute()


def get_or_enrich_company(
    company_id: str,
    company_name: str,
    *,
    domain: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    client = get_client()
    existing: dict[str, Any] = {}
    if client is not None:
        row = (
            client.table("companies")
            .select("id, name, domain, sector, stage, description, enrichment, enrichment_at")
            .eq("id", company_id)
            .limit(1)
            .execute()
        )
        if row.data:
            existing = row.data[0]
            enrich = existing.get("enrichment") or {}
            if not force and enrich.get("summary"):
                return {
                    "id": existing["id"],
                    "name": existing["name"],
                    "domain": existing.get("domain"),
                    "sector": existing.get("sector"),
                    "stage": existing.get("stage"),
                    "description": existing.get("description"),
                    "enrichment": enrich,
                }

    enrichment = enrich_company(company_name, domain=domain or existing.get("domain"))
    persist_company_enrichment(company_id, enrichment)

    # Light sector/stage heuristics from summary
    summary_l = (enrichment.get("summary") or "").lower()
    sector = existing.get("sector")
    stage = existing.get("stage")
    if not sector:
        for label in ("fintech", "saas", "devtools", "ai", "healthcare", "marketplace", "crypto"):
            if label in summary_l:
                sector = label
                break
    if not stage:
        for label in ("pre-seed", "seed", "series a", "series b"):
            if label in summary_l:
                stage = label.title().replace("Series A", "Series A")
                break

    if client is not None and (sector or stage):
        patch: dict[str, Any] = {}
        if sector:
            patch["sector"] = sector
        if stage:
            patch["stage"] = stage
        if patch:
            client.table("companies").update(patch).eq("id", company_id).execute()

    return {
        "id": company_id,
        "name": company_name,
        "domain": domain or existing.get("domain"),
        "sector": sector,
        "stage": stage,
        "description": enrichment.get("summary") or existing.get("description"),
        "enrichment": enrichment,
    }
