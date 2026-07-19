"""Agent D — Thesis Engine CRUD + VC Agent Chat.

Full spec: `docs/12-THESIS-SETTINGS-UI.md`, `docs/05-CURSOR-SKILLS.md`.

`POST /agent/message` is the single entry: search-shaped asks run the
natural-language query path; diligence/action asks route toward Cursor skills.
"""

from __future__ import annotations

import re

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from api.agent import memory_chat, nl_query, pipeline_stats, sourcing_sweep, thesis_store
from api.core.config import settings

router = APIRouter(tags=["thesis", "agent"])

_ACTION_RE = re.compile(
    r"\b("
    r"compare|verify|trust\s*score|genome|memo|proximity|wayback|"
    r"screen|channel\s*quality|what'?s|tell\s+me|how\s+(?:is|are|does)|"
    r"diligence|outreach"
    r")\b",
    re.IGNORECASE,
)

# "How many inbound leads today?" — honest counts from the opportunity store.
_STATS_RE = re.compile(
    r"(\bhow\s+many\b.*\b(?:leads?|inbound|deals?|applications?)\b)"
    r"|(\b(?:leads?|inbound|applications?)\b.*\btoday\b)",
    re.IGNORECASE,
)

# Unambiguous diligence-skill verbs. Checked BEFORE the memory intent so
# "compare X and Y based on our notes" still routes to skills; conversational
# action tokens ("tell me", "what's") stay lower priority than memory.
_HARD_ACTION_RE = re.compile(
    r"\b(compare|verify|trust\s*score|genome|memo|proximity|wayback|"
    r"channel\s*quality|diligence|outreach)\b",
    re.IGNORECASE,
)

# Chief-of-staff asks answered from the unified memory layer (notes, calls,
# commitments, decisions) rather than the live pipeline table.
_MEMORY_RE = re.compile(
    r"\b("
    r"catch\s+me\s+up|brief\s+me|remind\s+me|what\s+did\s+we|what\s+did\s+\w+\s+(?:say|agree|promise|commit)|"
    r"last\s+call|intro\s+call|notes?|discussed?|agreed?|outstanding|"
    r"commitments?|committed|promised?|follow[-\s]?ups?"
    r")\b",
    re.IGNORECASE,
)


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


def _is_action_intent(message: str) -> bool:
    return bool(_ACTION_RE.search(message or ""))


@router.post("/agent/message")
def agent_message(payload: dict):
    """Unified Ask entry: pipeline search OR diligence skill routing.

    Search (default): compound filters → `nl_query` with per-clause matches.
    Action: keyword-routed stub toward `.cursor/skills/*` until Wave 3.D
    wires the full Cursor skill runner.
    """
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(400, "message must not be empty")

    if _STATS_RE.search(message):
        stats = pipeline_stats.inbound_today()
        return {
            "mode": "stats",
            "reply": stats["reply"],
            "skills_used": ["pipeline-stats"],
            "citations": [],
            "search": None,
        }

    if _MEMORY_RE.search(message) and not _HARD_ACTION_RE.search(message):
        memo = memory_chat.answer(message)
        return {
            "mode": "memory",
            "reply": memo["reply"],
            "skills_used": ["memory-search", "memory-facts"] if memo["available"] else [],
            "citations": memo["citations"],
            "search": None,
        }

    if _is_action_intent(message):
        return {
            "mode": "action",
            "reply": (
                "That looks like a diligence action. Skill routing "
                "(compare, verify-claim, genome, memo, …) lands in Wave 3 — "
                f"for now try a pipeline filter like "
                f"“technical founder, AI infra, no prior VC backing”. "
                f"You asked: {message!r}"
            ),
            "skills_used": ["vc-agent-router"],
            "citations": [],
            "search": None,
        }

    result = nl_query.run(message)
    n = len(result.get("results") or [])
    constraints = result.get("constraints") or []
    top = (result.get("results") or [{}])[0] if n else {}
    top_bit = (
        f" Top match: {top.get('company_name')} "
        f"({top.get('match_count')}/{len(constraints)} clauses)."
        if n and top.get("company_name")
        else ""
    )
    return {
        "mode": "search",
        "reply": (
            f"Resolved {len(constraints)} constraint(s); "
            f"{n} opportunit{'y' if n == 1 else 'ies'} ranked with per-clause matches."
            f"{top_bit}"
        ),
        "skills_used": ["natural-language-query"],
        "citations": [],
        "search": result,
    }


class SourcingSweepPayload(BaseModel):
    thesis_id: str | None = None


@router.post("/skills/thesis-sourcing-sweep/run")
def run_sourcing_sweep(payload: SourcingSweepPayload = SourcingSweepPayload()):
    """Cursor skill `.cursor/skills/thesis-sourcing-sweep/SKILL.md`: active
    thesis -> structured Perplexity queries -> leads landed in Bronze."""
    return sourcing_sweep.run(payload.thesis_id)


@router.post("/skills/founder-sourcing-sweep/run")
def run_founder_sourcing_sweep(payload: SourcingSweepPayload = SourcingSweepPayload()):
    """Founder-first thesis sweep via Perplexity (+ Tavily) -> watchlist + enrichment."""
    return founder_sourcing_sweep.run(payload.thesis_id)


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
        "founder-sourcing-sweep",
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
