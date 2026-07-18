"""In-memory Thesis Engine store (Wave 1 stand-in for `thesis_profiles` table).

Seed values match `docs/12-THESIS-SETTINGS-UI.md` §6 and
`docs/14-SEED-DATA-SPEC.md` §1. Agent A replaces this with real Supabase
reads/writes in Wave 1 task 1.A without changing the router contract.
"""

from __future__ import annotations

import itertools
from typing import Any

_id_counter = itertools.count(1)

_THESES: list[dict[str, Any]] = [
    {
        "id": "thesis-ai-infra-eu",
        "name": "Pre-seed AI Infra EU",
        "version": 1,
        "is_active": True,
        "sectors": ["ai_infra", "devtools"],
        "stage": "pre_seed",
        "geography": "EU",
        "check_size_usd": 100000,
        "ownership_target_pct": 5,
        "risk_appetite": "balanced",
        "exclude_sectors": ["crypto"],
        "require_signals": ["technical_founder"],
        "watchlist_promotion_threshold": 0.65,
        "notes": None,
    },
    {
        "id": "thesis-devtools-us",
        "name": "Aggressive US Seed DevTools",
        "version": 1,
        "is_active": False,
        "sectors": ["devtools", "developer_platforms"],
        "stage": "seed",
        "geography": "US",
        "check_size_usd": 100000,
        "ownership_target_pct": 7,
        "risk_appetite": "aggressive",
        "exclude_sectors": [],
        "require_signals": [],
        "watchlist_promotion_threshold": 0.45,
        "notes": None,
    },
]


def list_theses() -> list[dict[str, Any]]:
    return _THESES


def get_thesis(thesis_id: str) -> dict[str, Any] | None:
    return next((t for t in _THESES if t["id"] == thesis_id), None)


def get_active_thesis() -> dict[str, Any] | None:
    return next((t for t in _THESES if t["is_active"]), None)


def create_thesis(payload: dict[str, Any]) -> dict[str, Any]:
    thesis = {**payload, "id": f"thesis-{next(_id_counter)}", "version": 1}
    thesis.setdefault("is_active", False)
    _THESES.append(thesis)
    return thesis


def activate_thesis(thesis_id: str) -> dict[str, Any] | None:
    target = get_thesis(thesis_id)
    if target is None:
        return None
    for t in _THESES:
        t["is_active"] = t["id"] == thesis_id
    return target
