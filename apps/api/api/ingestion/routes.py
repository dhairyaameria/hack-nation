"""Agent B — inbound application + outbound ingestion entry points.

Wave 1: real deck parsing + fast screen, backed by the in-memory
`opportunity_store` (Wave 2 swaps that for Supabase — see
`docs/03-SOURCING.md`).

Inbound Perplexity rerank: `POST /inbound/rerank` — same function as the
cron job (`docs/19-INBOUND-RERANK.md`).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Form, UploadFile

from api.core import opportunity_store
from api.ingestion import deck_parser, deck_storage, fast_screen, inbound_rerank

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

    verdict, reason = fast_screen.screen(company_name, claims)

    opp = opportunity_store.create_opportunity(
        company_name=company_name,
        founder_name=founder_name,
        source="inbound",
        discovery_channel="direct_apply",
    )

    deck_meta: dict[str, str] = {}
    if file_bytes is not None:
        deck_meta = deck_storage.upload_deck(opp["id"], file_bytes, filename)
        opportunity_store.update_opportunity(opp["id"], **deck_meta)

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
        "deck_filename": deck_meta.get("deck_filename") or (deck.filename if deck else None),
        "deck_url": deck_meta.get("deck_url"),
        "deck_storage_path": deck_meta.get("deck_storage_path"),
        "claims_extracted": len(claims),
        "screen_verdict": verdict,
        "screen_reason": reason,
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


@router.post("/ingest/founder")
async def ingest_founder(payload: dict):
    return {"status": "accepted", "note": "Entity resolution stub — see Wave 1 task 1.A."}
