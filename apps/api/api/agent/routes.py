"""Agent D — Thesis Engine CRUD + VC Agent Chat stub.

Full spec: `docs/12-THESIS-SETTINGS-UI.md`, `docs/05-CURSOR-SKILLS.md`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.agent import nl_query, sourcing_sweep, thesis_store

router = APIRouter(tags=["thesis", "agent"])


@router.get("/thesis")
def list_thesis():
    return thesis_store.list_theses()


@router.post("/thesis", status_code=201)
def create_thesis(payload: dict):
    return thesis_store.create_thesis(payload)


@router.get("/thesis/active")
def get_active_thesis():
    thesis = thesis_store.get_active_thesis()
    if thesis is None:
        raise HTTPException(404, "No active thesis set")
    return thesis


@router.get("/thesis/{thesis_id}")
def get_thesis(thesis_id: str):
    thesis = thesis_store.get_thesis(thesis_id)
    if thesis is None:
        raise HTTPException(404, "Thesis not found")
    return thesis


@router.post("/thesis/{thesis_id}/activate")
def activate_thesis(thesis_id: str):
    thesis = thesis_store.activate_thesis(thesis_id)
    if thesis is None:
        raise HTTPException(404, "Thesis not found")
    return thesis


@router.post("/agent/message")
def agent_message(payload: dict):
    """VC Agent Chat stub — routes to `.cursor/skills/vc-agent-router` in Wave 3.

    Wave 1: echoes a placeholder so the frontend chat panel can be built
    against a real shape now.
    """
    message = payload.get("message", "")
    return {
        "reply": (
            "VC Agent Chat is not wired to Cursor Skills yet (Wave 3 task 3.D). "
            f"You asked: {message!r}"
        ),
        "skills_used": [],
        "citations": [],
    }


class SourcingSweepPayload(BaseModel):
    thesis_id: str | None = None


@router.post("/skills/thesis-sourcing-sweep/run")
def run_sourcing_sweep(payload: SourcingSweepPayload = SourcingSweepPayload()):
    """Cursor skill `.cursor/skills/thesis-sourcing-sweep/SKILL.md`: active
    thesis -> structured Perplexity queries -> leads landed in Bronze."""
    return sourcing_sweep.run(payload.thesis_id)


class NaturalLanguageQueryPayload(BaseModel):
    query: str


@router.post("/query/natural-language")
def natural_language_query(payload: NaturalLanguageQueryPayload):
    """Compound query -> structured constraints -> ranked opportunities
    with a per-clause match explanation for every result."""
    if not payload.query.strip():
        raise HTTPException(400, "query must not be empty")
    return nl_query.run(payload.query)


@router.get("/skills")
def list_skills():
    """Catalog mirror of `.cursor/skills/*/SKILL.md` — see `docs/01-CONTRACTS.md` §4."""
    return [
        "thesis-sourcing-sweep",
        "memo-research",
        "generate-memo",
        "verify-claim",
        "founder-genome-lookup",
        "network-proximity-check",
        "wayback-history",
        "screen-opportunity",
        "channel-quality-report",
        "compare-opportunities",
        "vc-agent-router",
    ]
