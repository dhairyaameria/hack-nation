"""Agent C — 3-axis scoring, trust, memo endpoints.

Backed by `opportunity_store` / `founder_store` / `thesis_store`, which are
Supabase-backed when credentials are configured and fall back to
fixtures/in-memory data otherwise (see `docs/17-PARALLEL-WORKFLOW.md` §4).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.agent import thesis_store
from api.core import founder_store, opportunity_store
from api.core.db import get_client
from api.ingestion import outbound_enrich
from api.intelligence import agents

router = APIRouter(tags=["intelligence"])


@router.get("/opportunities")
def list_opportunities():
    opps = opportunity_store.list_opportunities()
    active_thesis = thesis_store.get_active_thesis()
    return {
        "active_thesis": {"id": active_thesis["id"], "name": active_thesis["name"]} if active_thesis else None,
        "opportunities": opps,
    }


@router.get("/memos")
def list_memos():
    """Index of all generated investment memos (required sections + gap counts)."""
    return {"memos": opportunity_store.list_memos()}


@router.get("/portfolio")
def list_portfolio():
    """Funded portfolio companies — closed $100K yes decisions."""
    return {"companies": opportunity_store.list_portfolio()}


@router.get("/opportunity/{opportunity_id}")
def get_opportunity(opportunity_id: str):
    detail = opportunity_store.get_opportunity(opportunity_id)
    if detail is None:
        raise HTTPException(404, "Opportunity not found")
    return detail


def _github_hint_for_founder(founder_id: str | None) -> str | None:
    """Use founders.source_entity_id when it looks like a GitHub login."""
    if not founder_id:
        return None
    client = get_client()
    if client is None:
        return None
    res = (
        client.table("founders")
        .select("source_entity_id")
        .eq("id", founder_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    sid = (res.data[0].get("source_entity_id") or "").strip()
    if sid and " " not in sid and "/" not in sid and len(sid) < 40:
        return sid
    return None


@router.post("/opportunity/{opportunity_id}/analyze")
def analyze_opportunity(opportunity_id: str):
    """Research-first diligence: gather public signals (GitHub, LinkedIn, HN,
    arXiv, Perplexity, Tavily) → provisional claims → Analyst → Validator →
    Referee. Deck-less outbound opportunities are first-class.
    """
    opp = opportunity_store.get_opportunity(opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")

    founder_name = opp.get("founder_name") or "Unknown founder"
    company_name = opp.get("company_name") or "Unknown company"
    existing = opp.get("claims") or []

    # Always refresh live research — outbound shells have zero deck claims;
    # inbound decks still benefit from corroborating public signals.
    enrichment = outbound_enrich.enrich_for_analysis(
        founder_name=founder_name,
        company_name=company_name,
        existing_claims=existing,
        github_username=_github_hint_for_founder(opp.get("founder_id")),
    )
    if not enrichment["claims"] and not existing:
        raise HTTPException(
            422,
            "No public research or deck claims available to analyze. "
            "Check Perplexity/Tavily keys or add a deck.",
        )

    # Persist new research claims BEFORE the pipeline so Validator writes
    # attach to real claim UUIDs (not ephemeral ids).
    existing_texts = {(c.get("text") or "").strip().lower() for c in existing}
    to_insert = []
    for c in enrichment["claims"]:
        text = (c.get("text") or "").strip()
        if not text or text.lower() in existing_texts:
            continue
        to_insert.append({
            "text": text,
            "slide_locator": c.get("slide_locator") or "outbound_research",
            "source": "outbound_research",
        })
    if to_insert:
        opportunity_store.update_opportunity(opportunity_id, claims=to_insert)
        opp = opportunity_store.get_opportunity(opportunity_id) or opp

    claims = [
        {
            "claim_id": c["claim_id"],
            "text": c["text"],
            "slide_locator": c.get("slide_locator") or "outbound_research",
        }
        for c in (opp.get("claims") or [])
        if c.get("text")
    ]
    if not claims:
        raise HTTPException(422, "Research produced no persistable claims")

    result = agents.run_pipeline(
        opportunity_id,
        company_name,
        claims,
        founder_id=opp.get("founder_id"),
        founder_name=founder_name,
        research_blob=enrichment.get("research_blob") or "",
    )
    result["research_channels"] = [s.get("channel") for s in enrichment.get("signals") or [] if s.get("channel")]

    opportunity_store.update_opportunity(
        opportunity_id,
        axis_scores=result["axis_scores"],
        memo=result["memo"],
        claims=result["claims"],
        trace=result["trace"],
        status="diligence",
    )
    opportunity_store.set_sla_stage(opportunity_id, "diligence_at")

    return {"opportunity_id": opportunity_id, "status": "analyzed", **result}


@router.get("/opportunity/{opportunity_id}/trust")
def get_trust(opportunity_id: str):
    opp = opportunity_store.get_opportunity(opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")
    return {"claims": opp.get("claims", [])}


@router.get("/opportunity/{opportunity_id}/memo")
def get_memo(opportunity_id: str):
    opp = opportunity_store.get_opportunity(opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")
    return opp.get("memo")


@router.get("/recommendation/{opportunity_id}/trace")
def get_trace(opportunity_id: str):
    if opportunity_store.get_opportunity(opportunity_id) is None:
        raise HTTPException(404, "Opportunity not found")
    trace = opportunity_store.get_trace(opportunity_id)
    if trace is None:
        raise HTTPException(404, "No reasoning trace yet — run /analyze first.")
    return trace


@router.get("/founders/{founder_id}")
def get_founder(founder_id: str):
    profile = founder_store.get_founder_profile(founder_id)
    if profile is None:
        raise HTTPException(404, "Founder not found")
    return profile


@router.get("/founders/{founder_id}/network")
def get_founder_network(founder_id: str):
    graph = founder_store.get_network_graph(founder_id)
    if graph is None:
        raise HTTPException(404, "No network graph for this founder yet.")
    return graph
