"""Agent B — inbound application + outbound ingestion entry points.

Real deck parsing + fast screen for inbound, backed by `opportunity_store`
(Supabase-backed, see `docs/03-SOURCING.md` §1). Outbound sourcing (§2-4:
GitHub/HN connectors, watchlist state machine, convergence into the same
application code path) lives in `api.ingestion.watchlist`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from api.core import opportunity_store
from api.ingestion import (
    deck_parser,
    deck_storage,
    deck_store,
    fast_screen,
    inbound_rerank,
    watchlist,
)

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
    file_bytes: bytes | None = None
    filename: str | None = None
    if deck is not None:
        file_bytes = await deck.read()
        filename = deck.filename
        claims = deck_parser.parse_deck(file_bytes)

    opp = opportunity_store.create_opportunity(
        company_name=company_name,
        founder_name=founder_name,
        source="inbound",
        discovery_channel="direct_apply",
    )
    dedupe = opp.get("dedupe") or {"action": "created"}
    attached = dedupe.get("action") == "attached"

    deck_meta: dict[str, str] = {}
    if file_bytes is not None:
        # Supabase Storage (shared across deploys) + local mirror for preview API
        deck_meta = deck_storage.upload_deck(opp["id"], file_bytes, filename)
        local_meta = deck_store.save_deck(opp["id"], file_bytes, filename)
        if not deck_meta.get("deck_storage_path"):
            deck_meta["deck_storage_path"] = local_meta["deck_storage_path"]
        if not deck_meta.get("deck_filename"):
            deck_meta["deck_filename"] = local_meta["deck_filename"]
        # Prefer API-served URL for iframe previews when Storage public URL is empty
        if not deck_meta.get("deck_url"):
            deck_meta["deck_url"] = f"/api/v1/inbound/applications/{opp['id']}/deck"

    if attached:
        # Reuse open deal: store deck + merge claims only. Do not rewrite
        # screen/status — Analyze / daily_pipeline own the heavy refresh.
        if deck_meta:
            opportunity_store.update_opportunity(opp["id"], **deck_meta)
        claims_added = opportunity_store.merge_provisional_claims(
            opp["id"],
            [{**c, "source": "deck"} for c in claims],
        )
        return {
            "opportunity_id": opp["id"],
            "company_id": opp.get("company_id"),
            "company_name": company_name,
            "deck_filename": deck_meta.get("deck_filename") or filename,
            "has_deck": bool(deck_meta) or bool(opp.get("has_deck")),
            "deck_url": deck_meta.get("deck_url")
            or opp.get("deck_url")
            or (f"/api/v1/inbound/applications/{opp['id']}/deck" if deck_meta else None),
            "deck_storage_path": deck_meta.get("deck_storage_path") or opp.get("deck_storage_path"),
            "claims_extracted": claims_added,
            "screen_verdict": opp.get("screen_verdict") or "needs-more-info",
            "screen_reason": (
                "Attached to existing open opportunity — deck/claims stored; "
                "re-screen and Analyze deferred."
            ),
            "dedupe": dedupe,
        }

    verdict, reason = fast_screen.screen(company_name, claims)
    opportunity_store.update_opportunity(
        opp["id"],
        claims=[{**c, "claim_id": f"claim-{i}"} for i, c in enumerate(claims)],
        screen_verdict=verdict,
        status="screening" if verdict == "pass" else "rejected" if verdict == "reject" else "needs-more-info",
        **deck_meta,
    )
    opportunity_store.set_sla_stage(opp["id"], "screening_at")

    return {
        "opportunity_id": opp["id"],
        "company_id": opp.get("company_id"),
        "company_name": company_name,
        "deck_filename": deck_meta.get("deck_filename") or filename,
        "has_deck": bool(deck_meta),
        "deck_url": deck_meta.get("deck_url")
        or (f"/api/v1/inbound/applications/{opp['id']}/deck" if deck_meta else None),
        "deck_storage_path": deck_meta.get("deck_storage_path"),
        "claims_extracted": len(claims),
        "screen_verdict": verdict,
        "screen_reason": reason,
        "dedupe": dedupe,
    }


@router.post("/inbound/rerank")
def rerank_inbound(payload: dict[str, Any] | None = Body(default=None)):
    """Manually trigger Perplexity rerank of all inbound opportunities.

    Same code path as the cron job (`jobs/pipelines/inbound_rerank_cron.py`).
    Optional body: `{"trigger": "manual"}` (default). UI can call this from
    a button later — no UI assumptions here.
    """
    trigger = "manual"
    if isinstance(payload, dict) and payload.get("trigger") in {"manual", "cron", "api"}:
        trigger = payload["trigger"]
    return inbound_rerank.rerank_inbound(trigger=trigger)  # type: ignore[arg-type]


@router.get("/inbound/ranked")
def list_ranked_inbound():
    """Inbound opportunities ordered by latest `inbound_rank` (nulls last)."""
    rows = opportunity_store.list_inbound_for_rerank()
    rows.sort(
        key=lambda r: (
            r.get("inbound_rank") is None,
            r.get("inbound_rank") if r.get("inbound_rank") is not None else 10**9,
            r.get("company_name") or "",
        )
    )
    return {
        "count": len(rows),
        "opportunities": [
            {
                "id": r["id"],
                "company_name": r["company_name"],
                "founder_name": r["founder_name"],
                "screen_verdict": r.get("screen_verdict"),
                "status": r.get("status"),
                "thesis_fit_score": r.get("thesis_fit_score"),
                "inbound_rank": r.get("inbound_rank"),
                "inbound_rank_rationale": r.get("inbound_rank_rationale"),
                "deck_url": r.get("deck_url"),
                "deck_storage_path": r.get("deck_storage_path"),
            }
            for r in rows
        ],
    }


@router.get("/inbound/applications")
def list_inbound_applications():
    """Card grid for Inbound Sources — PDF preview + company deep-link."""
    return {"applications": opportunity_store.list_inbound()}


@router.get("/inbound/applications/{opportunity_id}/deck")
def get_inbound_deck(opportunity_id: str):
    opp = opportunity_store.get_opportunity(opportunity_id)
    if opp is None:
        raise HTTPException(404, "Opportunity not found")
    storage_path = opp.get("deck_storage_path")
    data = deck_store.read_deck_bytes(opportunity_id, storage_path)
    if data is None and storage_path:
        data = deck_storage.download_deck(storage_path)
    if not data:
        raise HTTPException(404, "Deck PDF not found")
    filename = opp.get("deck_filename") or "deck.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "private, max-age=300",
        },
    )


@router.get("/companies/{company_id}")
def get_company(company_id: str, enrich: bool = True):
    """Company profile with research enrichment + linked opportunities."""
    profile = opportunity_store.get_company_profile(company_id, enrich=enrich)
    if profile is None:
        raise HTTPException(404, "Company not found")
    return profile


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
    linkedin_url: str | None = None


@router.get("/sourcing/watchlist")
def get_watchlist():
    return {"entries": watchlist.list_watchlist()}


@router.post("/sourcing/discover")
def discover(payload: DiscoverPayload):
    """Runs outbound connectors (GitHub, HN, arXiv, LinkedIn, Perplexity,
    Tavily) for a candidate founder and creates a scored watchlist entry."""
    if not payload.founder_name.strip():
        raise HTTPException(400, "founder_name is required")
    return watchlist.discover(
        payload.founder_name,
        company_name=payload.company_name,
        github_username=payload.github_username,
        hn_query=payload.hn_query,
        linkedin_url=payload.linkedin_url,
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
