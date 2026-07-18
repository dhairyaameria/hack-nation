"""In-memory opportunities store (Wave 1 stand-in for the `opportunities`,
`claims`, `reasoning_traces` tables).

Seeded from `shared/fixtures/pipeline-dashboard.json` +
`opportunity-detail.json` so the dashboard has real seed data on boot, then
grows in-process as inbound applications are submitted and analyzed. Agent A
replaces this with real Supabase reads/writes without changing the function
signatures other routers call (`list_opportunities`, `get_opportunity`,
`create_opportunity`, `update_opportunity`).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from api.core import fixtures

_OPPORTUNITIES: dict[str, dict[str, Any]] | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed() -> dict[str, dict[str, Any]]:
    dashboard = fixtures.get_pipeline_dashboard()
    by_id = {o["id"]: {**o, "claims": [], "memo": None, "trace": None} for o in dashboard["opportunities"]}
    # opp-contradiction has full detail (claims + memo) in its own fixture file
    full_detail = fixtures._load("opportunity-detail")  # noqa: SLF001 — internal seed use
    if full_detail["id"] in by_id:
        by_id[full_detail["id"]].update({
            "claims": full_detail.get("claims", []),
            "memo": full_detail.get("memo"),
            "trace_id": full_detail.get("trace_id"),
        })
    return by_id


def _store() -> dict[str, dict[str, Any]]:
    global _OPPORTUNITIES
    if _OPPORTUNITIES is None:
        _OPPORTUNITIES = _seed()
    return _OPPORTUNITIES


def list_opportunities() -> list[dict[str, Any]]:
    return list(_store().values())


def get_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    return _store().get(opportunity_id)


def create_opportunity(
    *,
    company_name: str,
    founder_name: str,
    source: str = "inbound",
    discovery_channel: str | None = "direct_apply",
    triggering_signal: str | None = None,
) -> dict[str, Any]:
    opp_id = f"opp-{uuid.uuid4().hex[:8]}"
    founder_id = f"founder-{uuid.uuid4().hex[:8]}"
    row = {
        "id": opp_id,
        "company_name": company_name,
        "founder_name": founder_name,
        "founder_id": founder_id,
        "source": source,
        "discovery_channel": discovery_channel,
        "triggering_signal": triggering_signal,
        "screen_verdict": None,
        "thesis_fit_score": None,
        "status": "discovered",
        "has_contradiction": False,
        "axis_scores": [],
        "claims": [],
        "memo": None,
        "trace": None,
        "sla": {
            "signal_at": _now_iso(),
            "screening_at": None,
            "diligence_at": None,
            "decision_at": None,
        },
    }
    _store()[opp_id] = row
    return row


def update_opportunity(opportunity_id: str, **fields: Any) -> dict[str, Any] | None:
    row = _store().get(opportunity_id)
    if row is None:
        return None
    row.update(fields)
    return row


def set_sla_stage(opportunity_id: str, stage: str) -> None:
    row = _store().get(opportunity_id)
    if row is not None and row.get("sla", {}).get(stage) is None:
        row.setdefault("sla", {})[stage] = _now_iso()
