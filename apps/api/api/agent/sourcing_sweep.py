"""Backing implementation for `.cursor/skills/thesis-sourcing-sweep/SKILL.md`
(`docs/05-CURSOR-SKILLS.md` §2): active thesis -> structured Perplexity
queries -> leads landed in Bronze via `ingest_raw`.

Leads are explicitly watchlist candidates, NOT pre-trusted facts — nothing
here writes to `founders`/`opportunities` directly. A human (or the
`/sourcing/discover` flow) still decides whether to act on a lead.
"""

from __future__ import annotations

from typing import Any

from api.agent import perplexity, thesis_store
from api.ingestion import memory


def _build_queries(thesis: dict[str, Any]) -> list[str]:
    sectors = ", ".join(thesis.get("sectors", [])) or "early-stage technology"
    geography = thesis.get("geography", "")
    stage = (thesis.get("stage", "") or "").replace("_", "-")
    where = f" based in {geography}" if geography else ""

    return [
        f"Recent {stage}-stage startup launches in {sectors}{where} in the last 3 months, with named founders.",
        f"Technical founders working in {sectors}{where} who recently posted about fundraising, hiring, or a product launch.",
        f"Hackathon or accelerator cohort results in {sectors} relevant to{where or ' any region'} in the past year.",
    ]


def run(thesis_id: str | None = None) -> dict[str, Any]:
    thesis = thesis_store.get_thesis(thesis_id) if thesis_id else thesis_store.get_active_thesis()
    if thesis is None:
        return {"thesis": None, "leads": [], "error": "No active thesis configured — set one in Settings first."}

    if not perplexity.is_available():
        return {
            "thesis": thesis["name"],
            "leads": [],
            "error": "PERPLEXITY_API_KEY not configured — the sourcing sweep needs it to run live research.",
        }

    leads = []
    for query in _build_queries(thesis):
        result = perplexity.research(query)
        if result is None:
            continue
        bronze_row = memory.ingest_raw(
            "perplexity",
            {"query": query, "answer": result["answer"], "citations": result["citations"]},
            entity_type="sourcing_lead",
        )
        leads.append({
            "query": query,
            "answer": result["answer"],
            "evidence": result["evidence"],
            "bronze_id": bronze_row["id"],
        })

    return {
        "thesis": thesis["name"],
        "thesis_id": thesis["id"],
        "leads": leads,
        "error": None if leads else "Perplexity returned no usable results for any query this run.",
    }
