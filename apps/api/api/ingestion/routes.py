"""Agent B — inbound application + outbound ingestion entry points.

Wave 1: minimal stub so the inbound form can post somewhere real.
Full deck parsing + fast screen lands in task 1.B / 2.B per
`docs/03-SOURCING.md`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Form, UploadFile

router = APIRouter(tags=["ingestion"])


@router.post("/application/submit")
async def submit_application(company_name: str = Form(...), deck: UploadFile | None = None):
    opportunity_id = f"opp-{uuid.uuid4().hex[:8]}"
    deck_name = deck.filename if deck else None
    return {
        "opportunity_id": opportunity_id,
        "company_name": company_name,
        "deck_filename": deck_name,
        "status": "received",
        "note": "Deck parsing + fast screen not wired yet (Wave 1 task 1.B).",
    }


@router.post("/ingest/founder")
async def ingest_founder(payload: dict):
    return {"status": "accepted", "note": "Entity resolution stub — see Wave 1 task 1.A."}
