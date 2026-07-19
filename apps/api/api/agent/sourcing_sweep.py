"""Backing implementation for `.cursor/skills/thesis-sourcing-sweep/SKILL.md`
(`docs/05-CURSOR-SKILLS.md` §2): active thesis -> structured Perplexity
queries -> Bronze + watchlist candidates.

Leads are watchlist candidates, NOT pre-trusted facts / opportunities.
A human still promotes and activates.
"""

from __future__ import annotations

from typing import Any

from api.agent import perplexity, thesis_store
from api.ingestion import memory, outbound_enrich, watchlist


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
        return {"thesis": None, "leads": [], "watchlist_entries": [], "error": "No active thesis configured — set one in Settings first."}

    if not perplexity.is_available():
        return {
            "thesis": thesis["name"],
            "leads": [],
            "watchlist_entries": [],
            "error": "PERPLEXITY_API_KEY not configured — the sourcing sweep needs it to run live research.",
        }

    leads = []
    watchlist_entries = []
    seen_pairs: set[tuple[str, str]] = set()

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

        candidates = outbound_enrich.extract_sweep_candidates(result["answer"], max_candidates=3)
        for cand in candidates:
            key = (cand["founder_name"].lower(), cand["company_name"].lower())
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            try:
                entry = watchlist.ingest_sweep_lead(
                    cand["founder_name"],
                    cand["company_name"],
                    answer=result["answer"],
                    citations=result["citations"],
                    evidence=result["evidence"],
                    bronze_id=bronze_row["id"],
                )
                watchlist_entries.append(entry)
            except Exception as exc:  # noqa: BLE001 — one bad lead must not kill the sweep
                print(f"[sourcing_sweep] failed to land {cand}: {exc}")

    return {
        "thesis": thesis["name"],
        "thesis_id": thesis["id"],
        "leads": leads,
        "watchlist_entries": watchlist_entries,
        "error": None if leads else "Perplexity returned no usable results for any query this run.",
    }
