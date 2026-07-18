"""Thesis Engine store — backed by the real `thesis_profiles` table when
Supabase is configured, otherwise an in-memory fallback (matches
`docs/12-THESIS-SETTINGS-UI.md` §6 seed values) so the API still boots
without credentials.
"""

from __future__ import annotations

import itertools
from typing import Any

from api.core.db import get_client

_id_counter = itertools.count(1)

_FALLBACK: list[dict[str, Any]] = [
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
    client = get_client()
    if client is None:
        return _FALLBACK
    res = client.table("thesis_profiles").select("*").order("created_at").execute()
    return res.data


def get_thesis(thesis_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        return next((t for t in _FALLBACK if t["id"] == thesis_id), None)
    res = client.table("thesis_profiles").select("*").eq("id", thesis_id).limit(1).execute()
    return res.data[0] if res.data else None


def get_active_thesis() -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        return next((t for t in _FALLBACK if t["is_active"]), None)
    res = client.table("thesis_profiles").select("*").eq("is_active", True).limit(1).execute()
    return res.data[0] if res.data else None


def create_thesis(payload: dict[str, Any]) -> dict[str, Any]:
    client = get_client()
    if client is None:
        thesis = {**payload, "id": f"thesis-{next(_id_counter)}", "version": 1}
        thesis.setdefault("is_active", False)
        _FALLBACK.append(thesis)
        return thesis
    row = {**payload}
    row.setdefault("version", 1)
    row.setdefault("is_active", False)
    res = client.table("thesis_profiles").insert(row).execute()
    return res.data[0]


def activate_thesis(thesis_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        target = get_thesis(thesis_id)
        if target is None:
            return None
        for t in _FALLBACK:
            t["is_active"] = t["id"] == thesis_id
        return target

    target = get_thesis(thesis_id)
    if target is None:
        return None
    # Deactivate the current active thesis first — `one_active_thesis` is a
    # partial unique index, so two rows can't both be true at once.
    client.table("thesis_profiles").update({"is_active": False}).eq("is_active", True).execute()
    res = client.table("thesis_profiles").update({"is_active": True}).eq("id", thesis_id).execute()
    return res.data[0] if res.data else None
