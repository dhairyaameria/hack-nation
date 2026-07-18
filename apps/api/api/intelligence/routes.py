"""Agent C — 3-axis scoring, trust, memo endpoints.

Wave 1: read-only, fixture-backed (`docs/15-MOCK-FIXTURES.md`). Wave 2
replaces `api.core.fixtures` calls with real Supabase-backed scoring
per `docs/04-INTELLIGENCE-TRUST.md` without changing these signatures.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.core import fixtures

router = APIRouter(tags=["intelligence"])


@router.get("/opportunities")
def list_opportunities():
    """Pipeline dashboard feed. Not yet in `01-CONTRACTS.md` — added for
    Agent E's dashboard; propose formalizing per `docs/17-PARALLEL-WORKFLOW.md` §6.
    """
    return fixtures.get_pipeline_dashboard()


@router.get("/opportunity/{opportunity_id}")
def get_opportunity(opportunity_id: str):
    detail = fixtures.get_opportunity_detail(opportunity_id)
    if detail is None:
        raise HTTPException(404, "Opportunity not found")
    return detail


@router.post("/opportunity/{opportunity_id}/analyze")
def analyze_opportunity(opportunity_id: str):
    """Stub for the Analyst/Validator/Referee chain — see task 1.C / 2.C."""
    detail = fixtures.get_opportunity_detail(opportunity_id)
    if detail is None:
        raise HTTPException(404, "Opportunity not found")
    return {"opportunity_id": opportunity_id, "status": "queued", "detail": detail}


@router.get("/opportunity/{opportunity_id}/trust")
def get_trust(opportunity_id: str):
    detail = fixtures.get_opportunity_detail(opportunity_id)
    if detail is None:
        raise HTTPException(404, "Opportunity not found")
    return {"claims": detail.get("claims", [])}


@router.get("/opportunity/{opportunity_id}/memo")
def get_memo(opportunity_id: str):
    detail = fixtures.get_opportunity_detail(opportunity_id)
    if detail is None:
        raise HTTPException(404, "Opportunity not found")
    return detail.get("memo")


@router.get("/founders/{founder_id}")
def get_founder(founder_id: str):
    profile = fixtures.get_founder_profile(founder_id)
    if profile is None:
        raise HTTPException(404, "Founder not found")
    return profile
