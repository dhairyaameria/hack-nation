#!/usr/bin/env python3
"""Product 2 daily loop: sweep every opportunity, fast-screen the unscreened
ones, and run the full Analyst -> Validator -> Referee analysis on screened
passes. A thin orchestrator over existing api modules, no logic of its own.
Scheduling is just cron/manual for the hackathon (no Celery).

Run:

    make pipeline
    # or: cd apps/api && source .venv/bin/activate && python ../../jobs/pipelines/daily_pipeline.py

Works without Supabase credentials (falls back to fixture-backed in-memory
opportunities, same as the API). LLM/Tavily calls degrade to heuristics when
keys are missing, so the loop is always demoable.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Same path trick as running the API: make `api.*` importable from repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from api.core import opportunity_store  # noqa: E402
from api.ingestion import fast_screen  # noqa: E402
from api.intelligence import agents  # noqa: E402

# Bounds LLM/Tavily spend per run; a real scheduler would page through the rest tomorrow.
MAX_ANALYZE_PER_RUN = 2


def run_daily() -> None:
    opportunities = opportunity_store.list_opportunities()
    print(f"[pipeline] sweeping {len(opportunities)} opportunities")

    analyzed = 0
    for opp in opportunities:
        detail = opportunity_store.get_opportunity(opp["id"]) or {}
        claims = detail.get("claims", [])

        if opp.get("screen_verdict") is None:
            verdict, reason = fast_screen.screen(opp["company_name"], claims)
            status = "screening" if verdict == "pass" else "rejected" if verdict == "reject" else "needs-more-info"
            opportunity_store.update_opportunity(opp["id"], screen_verdict=verdict, status=status)
            print(f"[pipeline] screened {opp['company_name']}: {verdict} ({reason})")
            # Refresh the stale snapshot so a fresh pass is analyzable this run.
            opp = {**opp, "screen_verdict": verdict, "status": status}

        if opp.get("screen_verdict") == "pass" and opp.get("status") == "screening" and analyzed < MAX_ANALYZE_PER_RUN:
            result = agents.run_pipeline(
                opp["id"],
                opp["company_name"],
                claims,
                founder_id=opp.get("founder_id"),
                founder_name=opp.get("founder_name") or "",
            )
            opportunity_store.update_opportunity(
                opp["id"],
                axis_scores=result["axis_scores"],
                memo=result["memo"],
                claims=result["claims"],
                trace=result["trace"],
                status="diligence",
            )
            opportunity_store.set_sla_stage(opp["id"], "diligence_at")
            analyzed += 1
            print(f"[pipeline] analyzed {opp['company_name']}: {len(result['claims'])} claims, memo written")

    print(f"[pipeline] done: {analyzed} analyzed this run (cap {MAX_ANALYZE_PER_RUN})")


if __name__ == "__main__":
    run_daily()
