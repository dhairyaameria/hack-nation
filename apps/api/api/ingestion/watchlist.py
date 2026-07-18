"""Watchlist state machine (`docs/03-SOURCING.md` §3-4):

    discovered -> scored -> activation-candidate -> outreach-sent -> applied -> screening

Promotion requires the conviction score to cross the active thesis's
threshold AND multiple independent corroborating signals — a single
strong signal stays on the watchlist. Activation converges into the
exact same `opportunity_store.create_opportunity` code path used by
native inbound applications (§3 "Convergence").
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from api.agent import thesis_store
from api.core import opportunity_store
from api.core.db import get_client
from api.ingestion import memory
from api.ingestion.connectors import github, hackernews

_MEMORY: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Cold-start-aware conviction scoring
# ---------------------------------------------------------------------------


def _score_signals(signals: list[dict[str, Any]]) -> tuple[float | None, float, str]:
    """Returns (conviction_score, confidence, rationale). No signals is
    `unknown` (None), never a low/bad score — absence of evidence is not
    evidence of absence (`docs/00-OVERVIEW.md` §4 rule 3/6)."""
    if not signals:
        return None, 0.15, "No public footprint found on any connector yet — cold start, unscored rather than penalized."

    weighted_total = 0.0
    weight_sum = 0.0
    parts = []
    for s in signals:
        if s["channel"] == "github":
            gh_score = min(1.0, (s.get("total_stars", 0) / 200) * 0.5 + (s.get("repos_pushed_last_90d", 0) / 5) * 0.5)
            weighted_total += gh_score * 0.6
            weight_sum += 0.6
            parts.append(f"GitHub: {s.get('own_repo_count', 0)} repos, {s.get('total_stars', 0)} stars, {s.get('repos_pushed_last_90d', 0)} pushed in last 90d")
        elif s["channel"] == "hackernews":
            hn_score = min(1.0, s.get("total_points", 0) / 200)
            weighted_total += hn_score * 0.4
            weight_sum += 0.4
            parts.append(f"HN: {s.get('story_count', 0)} stories, {s.get('total_points', 0)} points, top: {s.get('top_story_title')!r}")

    conviction = round(weighted_total / weight_sum, 2) if weight_sum else None
    confidence = round(min(0.9, 0.3 + 0.3 * len(signals)), 2)
    rationale = "; ".join(parts) if parts else "Signal found but not enough structure to score confidently."
    return conviction, confidence, rationale


# ---------------------------------------------------------------------------
# CRUD (Supabase-backed, in-memory fallback)
# ---------------------------------------------------------------------------


def _row_out(row: dict[str, Any], founder_name: str, company_name: str | None) -> dict[str, Any]:
    return {
        "id": row["id"],
        "founder_id": row["founder_id"],
        "founder_name": founder_name,
        "company_id": row.get("company_id"),
        "company_name": company_name,
        "stage": row["stage"],
        "conviction_score": row.get("conviction_score"),
        "promoted_via": row.get("promoted_via"),
        "signals": row.get("signals", []),
        "triggering_signal": row.get("triggering_signal"),
        "opportunity_id": row.get("opportunity_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def list_watchlist() -> list[dict[str, Any]]:
    client = get_client()
    if client is None:
        return [_row_out(r, r["_founder_name"], r.get("_company_name")) for r in _MEMORY.values()]
    res = (
        client.table("watchlist_entries")
        .select("*, founders(display_name), companies(name)")
        .order("created_at", desc=True)
        .execute()
    )
    return [
        _row_out(r, (r.get("founders") or {}).get("display_name", "Unknown"), (r.get("companies") or {}).get("name"))
        for r in res.data
    ]


def get_entry(entry_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        r = _MEMORY.get(entry_id)
        return _row_out(r, r["_founder_name"], r.get("_company_name")) if r else None
    res = (
        client.table("watchlist_entries")
        .select("*, founders(display_name), companies(name)")
        .eq("id", entry_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    r = res.data[0]
    return _row_out(r, (r.get("founders") or {}).get("display_name", "Unknown"), (r.get("companies") or {}).get("name"))


def _update_entry(entry_id: str, **fields: Any) -> None:
    client = get_client()
    if client is None:
        _MEMORY[entry_id].update(fields)
        return
    client.table("watchlist_entries").update({**fields, "updated_at": _now_iso()}).eq("id", entry_id).execute()


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


def discover(
    founder_name: str,
    *,
    company_name: str | None = None,
    github_username: str | None = None,
    hn_query: str | None = None,
) -> dict[str, Any]:
    """Runs connectors, resolves identity, and creates a `scored` watchlist
    entry in one call (discover -> scored is deterministic and cheap
    enough to collapse into a single request for the demo)."""
    founder = memory.resolve_founder(founder_name, source="github" if github_username else None, source_entity_id=github_username)
    company = memory.resolve_company(company_name) if company_name else None

    signals: list[dict[str, Any]] = []
    gh = github.fetch_profile_signals(github_username) if github_username else None
    if gh:
        signals.append({"channel": "github", **gh})
    hn = hackernews.fetch_launch_signals(hn_query or company_name or founder_name)
    if hn:
        signals.append({"channel": "hackernews", **hn})

    conviction_score, confidence, rationale = _score_signals(signals)
    stage = "scored" if signals else "discovered"

    client = get_client()
    if client is None:
        entry_id = f"watchlist-{uuid.uuid4().hex[:8]}"
        row = {
            "id": entry_id,
            "founder_id": founder["id"],
            "company_id": company["id"] if company else None,
            "stage": stage,
            "conviction_score": conviction_score,
            "signals": signals,
            "source": "github" if github_username else "hackernews",
            "source_entity_id": github_username or hn_query,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "_founder_name": founder_name,
            "_company_name": company_name,
        }
        _MEMORY[entry_id] = row
        out = _row_out(row, founder_name, company_name)
    else:
        row = {
            "founder_id": founder["id"],
            "company_id": company["id"] if company else None,
            "stage": stage,
            "conviction_score": conviction_score,
            "signals": signals,
            "source": "github" if github_username else "hackernews",
            "source_entity_id": github_username or hn_query,
        }
        created = client.table("watchlist_entries").insert(row).execute().data[0]
        out = _row_out(created, founder_name, company_name)

    out["confidence"] = confidence
    out["rationale"] = rationale
    return out


def promote(entry_id: str) -> dict[str, Any]:
    entry = get_entry(entry_id)
    if entry is None:
        raise ValueError("Watchlist entry not found.")

    active_thesis = thesis_store.get_active_thesis()
    threshold = active_thesis["watchlist_promotion_threshold"] if active_thesis else 0.65
    signals = entry.get("signals") or []
    score = entry.get("conviction_score")

    if score is None:
        return {**entry, "promoted": False, "reason": "Cold start — no scoreable signal yet. Not penalized, just not eligible for promotion."}
    if len(signals) < 2:
        return {**entry, "promoted": False, "reason": f"Only {len(signals)} independent signal(s) found — promotion requires multi-signal corroboration (≥2)."}
    if score < threshold:
        return {**entry, "promoted": False, "reason": f"Conviction score {score} is below the active thesis's promotion threshold {threshold}."}

    channels = sorted({s["channel"] for s in signals})
    promoted_via = "multi_signal:" + "+".join(channels)
    _update_entry(entry_id, stage="activation-candidate", promoted_via=promoted_via)
    updated = get_entry(entry_id)
    return {**updated, "promoted": True, "reason": f"Conviction {score} ≥ threshold {threshold} with {len(signals)} corroborating signals ({', '.join(channels)})."}


def generate_outreach(entry_id: str) -> dict[str, Any]:
    entry = get_entry(entry_id)
    if entry is None:
        raise ValueError("Watchlist entry not found.")
    if entry["stage"] != "activation-candidate":
        raise ValueError(f"Entry must be 'activation-candidate' before outreach (currently '{entry['stage']}').")

    signals = entry.get("signals") or []
    top_signal = max(signals, key=lambda s: s.get("total_stars", 0) + s.get("total_points", 0)) if signals else None
    if top_signal and top_signal["channel"] == "github":
        trigger_summary = f"GitHub activity ({top_signal.get('total_stars', 0)} stars, {top_signal.get('repos_pushed_last_90d', 0)} repos pushed in 90d)"
        draft = (
            f"Hi {entry['founder_name']},\n\n"
            f"I came across your GitHub profile ({top_signal.get('profile_url', '')}) — the pace of shipping "
            f"({top_signal.get('repos_pushed_last_90d', 0)} repos pushed in the last 90 days, "
            f"{top_signal.get('total_stars', 0)} stars) caught our attention.\n\n"
            f"We invest in {entry['company_name'] or 'early-stage teams'} at the pre-seed/seed stage. "
            f"Open to a 20-minute call this week?\n\n— VC Brain"
        )
    elif top_signal and top_signal["channel"] == "hackernews":
        trigger_summary = f"HN traction ({top_signal.get('total_points', 0)} points on {top_signal.get('top_story_title')!r})"
        draft = (
            f"Hi {entry['founder_name']},\n\n"
            f"Saw the Hacker News discussion on {top_signal.get('top_story_title')!r} "
            f"({top_signal.get('top_story_points', 0)} points) — congrats on the traction.\n\n"
            f"We invest in {entry['company_name'] or 'early-stage teams'} at the pre-seed/seed stage. "
            f"Open to a 20-minute call this week?\n\n— VC Brain"
        )
    else:
        trigger_summary = "multi-signal corroboration"
        draft = f"Hi {entry['founder_name']},\n\nWe've been tracking your work and would love to connect.\n\n— VC Brain"

    _update_entry(entry_id, stage="outreach-sent", triggering_signal=trigger_summary)
    updated = get_entry(entry_id)
    return {**updated, "draft": draft}


def activate(entry_id: str) -> dict[str, Any]:
    """Convergence: creates a real opportunity through the SAME code path
    as `POST /application/submit`, then advances the watchlist entry
    through applied -> screening in lockstep."""
    entry = get_entry(entry_id)
    if entry is None:
        raise ValueError("Watchlist entry not found.")
    if entry["stage"] not in {"activation-candidate", "outreach-sent"}:
        raise ValueError(f"Entry must be 'activation-candidate' or 'outreach-sent' to activate (currently '{entry['stage']}').")

    signals = entry.get("signals") or []
    primary_channel = signals[0]["channel"] if signals else "outbound"

    opp = opportunity_store.create_opportunity(
        company_name=entry["company_name"] or f"{entry['founder_name']}'s company",
        founder_name=entry["founder_name"],
        source="outbound",
        discovery_channel=primary_channel,
        triggering_signal=entry.get("triggering_signal") or entry.get("promoted_via"),
    )
    opportunity_store.update_opportunity(opp["id"], screen_verdict="pass", status="screening")
    opportunity_store.set_sla_stage(opp["id"], "screening_at")

    _update_entry(entry_id, stage="screening", opportunity_id=opp["id"])
    updated = get_entry(entry_id)
    return {**updated, "opportunity_id": opp["id"]}
