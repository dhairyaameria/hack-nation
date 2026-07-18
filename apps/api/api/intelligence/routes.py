"""Agent C — 3-axis scoring, trust, memo endpoints.

Backed by `opportunity_store` / `founder_store` / `thesis_store`, which are
Supabase-backed when credentials are configured and fall back to
fixtures/in-memory data otherwise (see `docs/17-PARALLEL-WORKFLOW.md` §4).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.agent import thesis_store
from api.core import founder_store, opportunity_store
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


@router.get("/opportunity/{opportunity_id}")
def get_opportunity(opportunity_id: str):
    detail = opportunity_store.get_opportunity(opportunity_id)
    if detail is None:
        raise HTTPException(404, "Opportunity not found")
    return detail


@router.post("/opportunity/{opportunity_id}/analyze")
def analyze_opportunity(opportunity_id: str):
    """Runs the Analyst -> Validator -> Referee chain (`api.intelligence.agents`)
    and persists axis scores + memo + reasoning trace onto the opportunity.
    """
    opp = opportunity_store.get_opportunity(opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")

    result = agents.run_pipeline(opportunity_id, opp["company_name"], opp.get("claims", []))

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
