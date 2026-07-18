"""Gold layer — feature-ready founder vectors (`docs/02-DATA-FOUNDATION.md`
§2, `docs/04-INTELLIGENCE-TRUST.md` §1). Two sources, in priority order:

1. A persisted `founder_genome_snapshots` row (an established/profiled
   founder — includes the bias-test pair).
2. A rough estimate derived on the fly from this founder's Bronze signals
   (`bronze_raw_events` — GitHub/HN connector output from
   `api.ingestion.watchlist`) for a founder discovered this session with
   no snapshot yet.

If neither exists, returns `None` — a true cold start with zero connector
data. That is a valid, common state, never converted into a low score
(`docs/00-OVERVIEW.md` §4 rule 3/6); the caller falls back to a claims-only
Founder axis instead.

`network_embeddedness` is a Genome dimension but is deliberately excluded
from the persistent Founder Score below — network proximity is capped and
separately labeled only at the point the Founder *axis* is computed, never
baked into the score that "persists forever" (§4 binding rule on network
never substituting for merit).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.core.db import get_client

NETWORK_AXIS_CAP = 0.15  # max share of the Founder axis network_embeddedness may contribute

FOUNDER_SCORE_WEIGHTS = {
    "execution_velocity": 0.30,
    "technical_depth": 0.25,
    "resilience_proxy": 0.25,
    "public_footprint_depth": 0.20,
}


def _today_midnight_iso() -> str:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()


def _from_bronze_signals(client, founder_id: str) -> dict[str, Any] | None:
    founder_res = client.table("founders").select("source_entity_id").eq("id", founder_id).limit(1).execute()
    if not founder_res.data or not founder_res.data[0].get("source_entity_id"):
        return None
    source_entity_id = founder_res.data[0]["source_entity_id"]

    bronze_res = (
        client.table("bronze_raw_events")
        .select("*")
        .eq("source_entity_id", source_entity_id)
        .order("fetched_at", desc=True)
        .execute()
    )
    if not bronze_res.data:
        return None

    github = next((r["payload"] for r in bronze_res.data if r["source"] == "github"), None)
    hn = next((r["payload"] for r in bronze_res.data if r["source"] == "hackernews"), None)
    if not github and not hn:
        return None

    execution_velocity, technical_depth, public_footprint_depth = 0.4, 0.4, 0.3
    if github:
        execution_velocity = min(1.0, (github.get("repos_pushed_last_90d") or 0) / 5)
        technical_depth = min(
            1.0,
            ((github.get("total_stars") or 0) / 300) * 0.6 + ((github.get("own_repo_count") or 0) / 15) * 0.4,
        )
        public_footprint_depth = min(1.0, (github.get("followers") or 0) / 500)
    if hn:
        public_footprint_depth = max(public_footprint_depth, min(1.0, (hn.get("total_points") or 0) / 300))

    return {
        "execution_velocity": round(execution_velocity, 2),
        "technical_depth": round(technical_depth, 2),
        "resilience_proxy": 0.5,  # no direct signal from a single connector snapshot — neutral, not penalized
        "public_footprint_depth": round(public_footprint_depth, 2),
        "network_embeddedness": 0.0,
        "confidence": 0.4,  # derived from Bronze, not a full Genome profile
        "derived_from": "bronze_signals",
    }


def get_gold_features(founder_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        return None

    genome_res = (
        client.table("founder_genome_snapshots")
        .select("*")
        .eq("founder_id", founder_id)
        .order("recorded_at", desc=True)
        .limit(1)
        .execute()
    )
    if genome_res.data:
        row = genome_res.data[0]
        return {
            "execution_velocity": row["execution_velocity"],
            "technical_depth": row["technical_depth"],
            "resilience_proxy": row["resilience_proxy"],
            "public_footprint_depth": row["public_footprint_depth"],
            "network_embeddedness": row.get("network_embeddedness") or 0.0,
            "confidence": row.get("confidence") or 0.5,
            "derived_from": "genome_snapshot",
        }

    return _from_bronze_signals(client, founder_id)


def compute_founder_score(gold: dict[str, Any]) -> float:
    """Founder Score v1 = weighted Gold features. Excludes
    network_embeddedness by design (see module docstring)."""
    return round(sum(gold.get(k, 0.0) * w for k, w in FOUNDER_SCORE_WEIGHTS.items()), 2)


def append_score_history(founder_id: str, score: float, confidence: float) -> None:
    """Appends to the founder's immutable score time series. Idempotent per
    UTC day (same convention as `db/seed/seed.py`) so repeated `/analyze`
    calls in one day don't spam duplicate rows — the series still only
    ever grows, never resets."""
    client = get_client()
    if client is None:
        return
    try:
        client.table("founder_score_history").upsert(
            {"founder_id": founder_id, "score": score, "confidence": confidence, "recorded_at": _today_midnight_iso()},
            on_conflict="founder_id,recorded_at",
        ).execute()
    except Exception as exc:  # noqa: BLE001 — scoring must never crash the pipeline
        print(f"[gold_features] failed to append founder_score_history: {exc}")


def get_score_trend(founder_id: str) -> str:
    client = get_client()
    if client is None:
        return "stable"
    res = (
        client.table("founder_score_history")
        .select("score")
        .eq("founder_id", founder_id)
        .order("recorded_at", desc=True)
        .limit(2)
        .execute()
    )
    rows = res.data or []
    if len(rows) < 2:
        return "stable"
    delta = rows[0]["score"] - rows[1]["score"]
    if delta > 0.02:
        return "improving"
    if delta < -0.02:
        return "declining"
    return "stable"


def founder_axis_from_gold(gold: dict[str, Any], founder_score: float, trend: str) -> dict[str, Any]:
    """Founder axis = 85% persistent-Founder-Score-blended Genome core +
    up to 15% network_embeddedness, capped and never allowed to dominate
    (`docs/03-SOURCING.md` §5, `docs/00-OVERVIEW.md` §4). This is what
    makes the bias test pass: a dense-but-shallow network can add at most
    0.15, never enough to outrank real execution."""
    genome_core = round(
        (
            gold.get("execution_velocity", 0)
            + gold.get("technical_depth", 0)
            + gold.get("resilience_proxy", 0)
            + gold.get("public_footprint_depth", 0)
        )
        / 4,
        2,
    )
    blended_core = round(0.5 * genome_core + 0.5 * founder_score, 2)
    network_raw = gold.get("network_embeddedness", 0.0)
    network_contribution = round(min(max(network_raw, 0.0), 1.0) * NETWORK_AXIS_CAP, 3)
    value = round(min(1.0, blended_core * (1 - NETWORK_AXIS_CAP) + network_contribution), 2)

    evidence = [
        {
            "source_type": "founder_score",
            "source_locator": "founder_score_history",
            "evidence_snippet": f"Persistent Founder Score {founder_score} (trend: {trend}), blended 50/50 with the latest Genome snapshot ({genome_core}).",
            "confidence": gold.get("confidence", 0.5),
        },
    ]
    if network_raw:
        evidence.append({
            "source_type": "network_proximity",
            "source_locator": "founder_genome_snapshots.network_embeddedness",
            "evidence_snippet": (
                f"Network proximity ({network_raw}) contributed {network_contribution} of the {value} axis "
                f"value — capped at {NETWORK_AXIS_CAP} of the total. Reflects who this founder is connected "
                "to, not their own demonstrated capability; always disclosed, never dominant."
            ),
            "confidence": gold.get("confidence", 0.5),
        })

    return {
        "axis": "founder",
        "value": value,
        "trend": trend,
        "confidence": gold.get("confidence", 0.5),
        "evidence": evidence,
    }
