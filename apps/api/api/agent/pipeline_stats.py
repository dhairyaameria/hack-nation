"""Pipeline stats for VC Agent Chat: counts computed straight from the
opportunity store (fixtures or Supabase). Numbers are never produced by an
LLM, so the chat can answer "how many inbound leads today?" without any
risk of fabrication (docs/00-OVERVIEW.md §4 rule 3).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.core import opportunity_store


def _arrival_date(opp: dict[str, Any]) -> str | None:
    signal_at = (opp.get("sla") or {}).get("signal_at")
    return signal_at[:10] if signal_at else None


def inbound_today() -> dict[str, Any]:
    today = datetime.now(timezone.utc).date().isoformat()
    opps = opportunity_store.list_opportunities()
    inbound = [o for o in opps if o.get("source") == "inbound"]
    todays = [o for o in inbound if _arrival_date(o) == today]

    if todays:
        names = ", ".join(
            f"{o.get('company_name')} (screen: {o.get('screen_verdict') or 'pending'})"
            for o in todays
        )
        reply = (
            f"{len(todays)} new inbound lead{'s' if len(todays) != 1 else ''} "
            f"arrived today: {names}. {len(inbound)} inbound total in the pipeline."
        )
    else:
        reply = (
            f"No new inbound leads arrived today. {len(inbound)} inbound "
            f"lead{'s' if len(inbound) != 1 else ''} total in the pipeline."
        )
    return {"reply": reply, "today_count": len(todays), "inbound_total": len(inbound)}
