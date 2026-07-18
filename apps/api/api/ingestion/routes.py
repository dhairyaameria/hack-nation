"""Agent B — inbound application + outbound ingestion entry points.

Real deck parsing + fast screen for inbound, backed by `opportunity_store`
(Supabase-backed, see `docs/03-SOURCING.md` §1). Outbound sourcing (§2-4:
GitHub/HN connectors, watchlist state machine, convergence into the same
application code path) lives in `api.ingestion.watchlist`.
"""

from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.core import opportunity_store
from api.ingestion import deck_parser, fast_screen, watchlist

router = APIRouter(tags=["ingestion"])


@router.post("/application/submit")
async def submit_application(
    company_name: str = Form(...),
    founder_name: str = Form("Unnamed founder"),
    deck: UploadFile | None = None,
):
    """Minimal-friction inbound: deck + company name. See
    docs/03-SOURCING.md §1 — do not add more required fields.
    """
    claims: list[dict[str, str]] = []
    if deck is not None:
        file_bytes = await deck.read()
        claims = deck_parser.parse_deck(file_bytes)

    verdict, reason = fast_screen.screen(company_name, claims)

    opp = opportunity_store.create_opportunity(
        company_name=company_name,
        founder_name=founder_name,
        source="inbound",
        discovery_channel="direct_apply",
    )
    opportunity_store.update_opportunity(
        opp["id"],
        claims=[{**c, "claim_id": f"claim-{i}"} for i, c in enumerate(claims)],
        screen_verdict=verdict,
        status="screening" if verdict == "pass" else "rejected" if verdict == "reject" else "needs-more-info",
    )
    opportunity_store.set_sla_stage(opp["id"], "screening_at")

    return {
        "opportunity_id": opp["id"],
        "company_name": company_name,
        "deck_filename": deck.filename if deck else None,
        "claims_extracted": len(claims),
        "screen_verdict": verdict,
        "screen_reason": reason,
    }


@router.post("/ingest/founder")
async def ingest_founder(payload: dict):
    return {"status": "accepted", "note": "Entity resolution stub — see Wave 1 task 1.A."}


# ---------------------------------------------------------------------------
# Outbound sourcing + watchlist (docs/03-SOURCING.md §2-4)
# ---------------------------------------------------------------------------


class DiscoverPayload(BaseModel):
    founder_name: str
    company_name: str | None = None
    github_username: str | None = None
    hn_query: str | None = None


@router.get("/sourcing/watchlist")
def get_watchlist():
    return {"entries": watchlist.list_watchlist()}


@router.post("/sourcing/discover")
def discover(payload: DiscoverPayload):
    """Runs GitHub + Hacker News connectors for a candidate founder,
    resolves identity, and creates a scored watchlist entry."""
    if not payload.github_username and not payload.hn_query and not payload.company_name:
        raise HTTPException(400, "Provide at least one of github_username, hn_query, or company_name to search a channel.")
    return watchlist.discover(
        payload.founder_name,
        company_name=payload.company_name,
        github_username=payload.github_username,
        hn_query=payload.hn_query,
    )


@router.post("/sourcing/watchlist/{entry_id}/promote")
def promote_entry(entry_id: str):
    try:
        return watchlist.promote(entry_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/sourcing/watchlist/{entry_id}/outreach")
def outreach_entry(entry_id: str):
    try:
        return watchlist.generate_outreach(entry_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/sourcing/watchlist/{entry_id}/activate")
def activate_entry(entry_id: str):
    """Convergence: creates a real opportunity through the same code path
    as `/application/submit`, then advances applied -> screening."""
    try:
        return watchlist.activate(entry_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
