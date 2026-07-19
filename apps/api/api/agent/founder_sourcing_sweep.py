"""Founder-first thesis sourcing — parallel to company thesis-sourcing-sweep.

Active thesis -> Perplexity founder-centric queries (+ optional Tavily) ->
watchlist candidates with founder enrichment. Leads are candidates, not
pre-trusted opportunities.
"""

from __future__ import annotations

from typing import Any

from api.agent import perplexity, thesis_store
from api.ingestion import memory, outbound_enrich, watchlist
from api.intelligence import retrieval


def _build_queries(thesis: dict[str, Any]) -> list[str]:
    sectors = ", ".join(thesis.get("sectors", [])) or "early-stage technology"
    geography = thesis.get("geography", "")
    stage = (thesis.get("stage", "") or "").replace("_", "-")
    where = f" based in {geography}" if geography else ""

    return [
        f"Notable technical founders building {stage}-stage startups in {sectors}{where} "
        f"who raised or launched in the last 12 months. Name each founder and company.",
        f"Second-time or resilient founders in {sectors}{where} with public track record "
        f"(prior exit, open-source, papers). Name founders and current companies.",
        f"Emerging AI/technical founders from accelerators or research labs relevant to "
        f"{sectors}{where}. Prefer named individuals with LinkedIn or GitHub.",
    ]


def run(thesis_id: str | None = None) -> dict[str, Any]:
    thesis = thesis_store.get_thesis(thesis_id) if thesis_id else thesis_store.get_active_thesis()
    if thesis is None:
        return {
            "thesis": None,
            "leads": [],
            "watchlist_entries": [],
            "error": "No active thesis configured — set one in Settings first.",
        }

    if not perplexity.is_available():
        return {
            "thesis": thesis["name"],
            "leads": [],
            "watchlist_entries": [],
            "error": "PERPLEXITY_API_KEY not configured — founder sourcing needs it to run live research.",
        }

    leads = []
    watchlist_entries = []
    seen_pairs: set[tuple[str, str]] = set()

    for query in _build_queries(thesis):
        result = perplexity.research(query)
        if result is None:
            continue

        tavily_hits = []
        if retrieval.is_available():
            tavily_hits = retrieval.search(query, max_results=4) or []

        bronze_row = memory.ingest_raw(
            "perplexity",
            {
                "query": query,
                "answer": result["answer"],
                "citations": result["citations"],
                "tavily": [
                    {"title": r.get("title"), "url": r.get("url"), "snippet": (r.get("content") or "")[:240]}
                    for r in tavily_hits
                    if r.get("url")
                ],
            },
            entity_type="founder_sourcing_lead",
        )
        leads.append({
            "query": query,
            "answer": result["answer"],
            "evidence": result["evidence"],
            "bronze_id": bronze_row["id"],
            "tavily_count": len(tavily_hits),
        })

        candidates = outbound_enrich.extract_sweep_candidates(result["answer"], max_candidates=4)
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
            except Exception as exc:  # noqa: BLE001
                print(f"[founder_sourcing_sweep] failed to land {cand}: {exc}")

    return {
        "thesis": thesis["name"],
        "thesis_id": thesis["id"],
        "leads": leads,
        "watchlist_entries": watchlist_entries,
        "error": None if leads else "Perplexity returned no usable results for any founder query this run.",
    }
