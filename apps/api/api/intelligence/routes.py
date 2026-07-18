"""Agent C — 3-axis scoring, trust, memo endpoints.

Backed by the in-memory `opportunity_store` (Wave 2 swaps that module for
Supabase-backed reads without changing these routes — see
`docs/17-PARALLEL-WORKFLOW.md` §4).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.core import fixtures, opportunity_store
from api.intelligence import agents

router = APIRouter(tags=["intelligence"])


@router.get("/opportunities")
def list_opportunities():
    opps = opportunity_store.list_opportunities()
    active_thesis = fixtures.get_active_thesis()
    return {
        "active_thesis": {"id": active_thesis["id"], "name": active_thesis["name"]},
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
        trace_id=result["trace"]["trace_id"],
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
    opp = opportunity_store.get_opportunity(opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")
    if opp.get("trace") is None:
        raise HTTPException(404, "No reasoning trace yet — run /analyze first.")
    return opp["trace"]


@router.get("/founders/{founder_id}")
def get_founder(founder_id: str):
    profile = fixtures.get_founder_profile(founder_id)
    if profile is None:
        raise HTTPException(404, "Founder not found")
    return profile
