"""Fixture-backed data access.

Wave 1 stand-in for real Supabase queries — see `docs/15-MOCK-FIXTURES.md`.
Every function here has a 1:1 real replacement planned for Wave 2
(`docs/08-IMPLEMENTATION-PLAN.md` task 2.E). Swap the body, keep the
signature, and downstream routers don't change.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from api.core.config import FIXTURES_DIR


@lru_cache(maxsize=None)
def _load(name: str) -> Any:
    path = FIXTURES_DIR / f"{name}.json"
    with path.open() as f:
        return json.load(f)


def get_pipeline_dashboard() -> dict[str, Any]:
    return _load("pipeline-dashboard")


def get_opportunity_detail(opportunity_id: str) -> dict[str, Any] | None:
    data = _load("opportunity-detail")
    if data.get("id") == opportunity_id:
        return data
    # Wave 1: only one fully-detailed fixture exists (opp-contradiction).
    # Fall back to a summary-only view for other seeded opportunities.
    dashboard = get_pipeline_dashboard()
    for opp in dashboard.get("opportunities", []):
        if opp["id"] == opportunity_id:
            return {**opp, "claims": [], "memo": None, "trace_id": None}
    return None


def get_founder_profile(founder_id: str) -> dict[str, Any] | None:
    data = _load("founder-profile")
    if data.get("id") == founder_id:
        return data
    return None


def get_network_graph_seed() -> dict[str, Any]:
    return _load("network-graph-seed")


def get_active_thesis() -> dict[str, Any]:
    return _load("thesis-active")
