"""Agent B — inbound application + outbound ingestion entry points.

Wave 1: real deck parsing + fast screen, backed by the in-memory
`opportunity_store` (Wave 2 swaps that for Supabase — see
`docs/03-SOURCING.md`).
"""

from __future__ import annotations

from fastapi import APIRouter, Form, UploadFile

from api.core import opportunity_store
from api.ingestion import deck_parser, fast_screen

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
