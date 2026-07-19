"""Founder profile enrichment via Perplexity + Tavily (cited web research).

Mirrors company_enrich: public research with provenance URLs, persisted on
`founders.enrichment`, Bronze events, and (when possible) a Gold genome
snapshot + Founder Score history row.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.agent import perplexity
from api.core import gold_features
from api.core.db import get_client
from api.ingestion import memory
from api.intelligence import retrieval


def enrichment_from_bronze(client, founder: dict[str, Any]) -> dict[str, Any] | None:
    """Fallback when `founders.enrichment` is empty or migration 013 not applied."""
    ids = [x for x in {founder.get("source_entity_id"), founder.get("display_name")} if x]
    if not ids:
        return None
    pplx = None
    tavily = None
    for sid in ids:
        res = (
            client.table("bronze_raw_events")
            .select("source, payload, fetched_at")
            .eq("source_entity_id", sid)
            .in_("source", ["perplexity", "tavily"])
            .order("fetched_at", desc=True)
            .limit(10)
            .execute()
        )
        for row in res.data or []:
            if row["source"] == "perplexity" and not pplx:
                pplx = row["payload"]
            if row["source"] == "tavily" and not tavily:
                tavily = row["payload"]
        if pplx:
            break
    if not pplx and not tavily:
        return None
    web_results = []
    for r in (tavily or {}).get("results") or []:
        if r.get("url"):
            web_results.append({
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": (r.get("content") or r.get("snippet") or "")[:320],
            })
    citations = list((pplx or {}).get("citations") or [])
    for r in web_results:
        if r["url"] not in citations:
            citations.append(r["url"])
    return {
        "summary": (pplx or {}).get("answer") or "",
        "citations": citations[:16],
        "web_results": web_results[:8],
        "sources": (
            ["perplexity", "tavily"] if (pplx and web_results)
            else (["perplexity"] if pplx else ["tavily"])
        ),
        "disclaimer": (
            "Enriched from public web research (Perplexity/Tavily). "
            "Not a licensed LinkedIn or Crunchbase API feed."
        ),
    }


def enrich_founder(
    founder_name: str,
    *,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Return structured enrichment payload (always safe to store as jsonb)."""
    context = f", founder of {company_name}" if company_name else ""
    q = (
        f"Founder profile for {founder_name}{context}. "
        "Write a concise diligence brief using markdown headings (###) and "
        "bullet lists — avoid markdown tables. Cover: background and career, "
        "prior companies/exits if public, technical depth or domain expertise, "
        "notable public footprint (GitHub, papers, LinkedIn, press), education "
        "if known, and current company role. Prefer primary sources and "
        "reputable news. Keep citation markers like [1] inline where claims "
        "need sources. Say explicitly when something is unknown."
    )
    answer = ""
    citations: list[str] = []
    evidence: list[dict[str, Any]] = []

    research = perplexity.research(q)
    if research:
        answer = research.get("answer") or ""
        citations = list(research.get("citations") or [])[:12]
        evidence = list(research.get("evidence") or [])[:12]

    web_q = (
        f"{founder_name}"
        + (f" {company_name}" if company_name else "")
        + " founder biography OR LinkedIn OR GitHub"
    )
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
        "company_name": company_name,
        "disclaimer": (
            "Enriched from public web research (Perplexity/Tavily). "
            "Not a licensed LinkedIn or Crunchbase API feed."
        ),
    }


def _ingest_bronze(
    founder_name: str,
    enrichment: dict[str, Any],
    *,
    company_name: str | None = None,
) -> None:
    if enrichment.get("summary"):
        memory.ingest_raw(
            "perplexity",
            {
                "query": f"founder profile:{founder_name}",
                "answer": enrichment["summary"],
                "citations": enrichment.get("citations") or [],
                "company_name": company_name,
            },
            entity_type="founder_research",
            source_entity_id=founder_name,
        )
    web_results = enrichment.get("web_results") or []
    if web_results:
        memory.ingest_raw(
            "tavily",
            {
                "query": f"{founder_name} founder",
                "results": [
                    {"title": r.get("title"), "url": r.get("url"), "content": r.get("snippet")}
                    for r in web_results
                ],
            },
            entity_type="founder_web_search",
            source_entity_id=founder_name,
        )


def persist_founder_enrichment(founder_id: str, enrichment: dict[str, Any]) -> None:
    client = get_client()
    if client is None:
        return
    try:
        client.table("founders").update({
            "enrichment": enrichment,
            "enrichment_at": enrichment.get("enriched_at"),
        }).eq("id", founder_id).execute()
    except Exception as exc:  # noqa: BLE001 — migration 013 may not be applied yet
        print(f"[founder_enrich] persist enrichment skipped (run 013_founder_enrichment.sql): {exc}")


def _linked_company_name(client, founder_id: str) -> str | None:
    role = (
        client.table("founder_company_roles")
        .select("company_id, companies(name)")
        .eq("founder_id", founder_id)
        .limit(1)
        .execute()
    )
    if role.data:
        companies = role.data[0].get("companies")
        if isinstance(companies, dict) and companies.get("name"):
            return companies["name"]
    opp = (
        client.table("opportunities")
        .select("companies(name)")
        .eq("founder_id", founder_id)
        .limit(1)
        .execute()
    )
    if opp.data:
        companies = opp.data[0].get("companies")
        if isinstance(companies, dict) and companies.get("name"):
            return companies["name"]
    wl = (
        client.table("watchlist_entries")
        .select("company_id, companies(name)")
        .eq("founder_id", founder_id)
        .limit(1)
        .execute()
    )
    if wl.data:
        companies = wl.data[0].get("companies")
        if isinstance(companies, dict) and companies.get("name"):
            return companies["name"]
    return None


def refresh_genome_from_bronze(founder_id: str) -> dict[str, Any] | None:
    """Derive Gold from Bronze (including just-written research) and persist."""
    client = get_client()
    if client is None:
        return None
    # Prefer bronze-derived dims so a stale genome snapshot doesn't block refresh.
    gold = gold_features._from_bronze_signals(client, founder_id)
    if not gold:
        gold = gold_features.get_gold_features(founder_id)
    if not gold:
        return None
    gold_features.upsert_genome_snapshot(founder_id, gold)
    score = gold_features.compute_founder_score(gold)
    gold_features.append_score_history(founder_id, score, gold.get("confidence") or 0.45)
    return gold


def get_or_enrich_founder(
    founder_id: str,
    *,
    force: bool = False,
    company_name: str | None = None,
) -> dict[str, Any]:
    client = get_client()
    existing: dict[str, Any] = {}
    if client is not None:
        try:
            row = (
                client.table("founders")
                .select("id, display_name, location, domain_affinity, enrichment, enrichment_at, source")
                .eq("id", founder_id)
                .limit(1)
                .execute()
            )
        except Exception:
            row = (
                client.table("founders")
                .select("id, display_name, location, domain_affinity, source")
                .eq("id", founder_id)
                .limit(1)
                .execute()
            )
        if not row.data:
            raise KeyError(founder_id)
        existing = row.data[0]
        enrich = existing.get("enrichment") or {}
        if not force and not enrich.get("summary"):
            # Migration 013 may be missing — reuse Bronze research if present.
            bronze_enrich = enrichment_from_bronze(client, existing)
            if bronze_enrich and bronze_enrich.get("summary"):
                enrich = bronze_enrich
        if not force and enrich.get("summary"):
            return {
                "id": existing["id"],
                "display_name": existing["display_name"],
                "location": existing.get("location"),
                "domain_affinity": existing.get("domain_affinity") or [],
                "enrichment": enrich,
            }
        if not company_name:
            company_name = _linked_company_name(client, founder_id)

    name = existing.get("display_name") or "Unknown founder"
    enrichment = enrich_founder(name, company_name=company_name)
    persist_founder_enrichment(founder_id, enrichment)
    _ingest_bronze(name, enrichment, company_name=company_name)

    # Domain affinity heuristic from summary text
    summary_l = (enrichment.get("summary") or "").lower()
    affinity = list(existing.get("domain_affinity") or [])
    if not affinity:
        for sector in ("ai", "devtools", "fintech", "healthcare", "saas", "infra", "crypto"):
            if sector in summary_l:
                affinity.append({
                    "sector": sector,
                    "weight": 0.7,
                    "confidence": 0.4,
                    "evidence_source": "perplexity",
                })
                break
        if affinity and client is not None:
            client.table("founders").update({"domain_affinity": affinity}).eq("id", founder_id).execute()

    refresh_genome_from_bronze(founder_id)

    return {
        "id": founder_id,
        "display_name": name,
        "location": existing.get("location"),
        "domain_affinity": affinity,
        "enrichment": enrichment,
    }
