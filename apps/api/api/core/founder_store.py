"""Founder profile + network graph reads — backed by `founders`,
`founder_genome_snapshots`, `founder_score_history`,
`network_proximity_scores`, `network_nodes`/`network_edges`.

Falls back to `shared/fixtures/founder-profile.json` /
`network-graph-seed.json` when Supabase isn't configured, so the UI still
demos without credentials (see `docs/15-MOCK-FIXTURES.md`).
"""

from __future__ import annotations

from typing import Any

from api.core import fixtures
from api.core.db import get_client

DISCLOSURE_TEXT = (
    "Network proximity signal — reflects who this founder is connected to, "
    "not their own demonstrated capability. Shown for transparency, weighted conservatively."
)


def _score_trend(history: list[dict[str, Any]]) -> str:
    if len(history) < 2:
        return "stable"
    delta = history[-1]["score"] - history[-2]["score"]
    if delta > 0.02:
        return "improving"
    if delta < -0.02:
        return "declining"
    return "stable"


def _genome_dimension(row: dict[str, Any], field: str) -> dict[str, Any]:
    return {
        "value": row[field],
        "trend": row.get(f"{field}_trend", "stable"),
        "confidence": row.get("confidence"),
        "evidence": [],
    }


def get_founder_profile(founder_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        return fixtures.get_founder_profile(founder_id)

    founder_res = client.table("founders").select("*").eq("id", founder_id).limit(1).execute()
    if not founder_res.data:
        return None
    founder = founder_res.data[0]

    history_res = (
        client.table("founder_score_history")
        .select("recorded_at, score")
        .eq("founder_id", founder_id)
        .order("recorded_at")
        .execute()
    )
    history = history_res.data or []

    genome_res = (
        client.table("founder_genome_snapshots")
        .select("*")
        .eq("founder_id", founder_id)
        .order("recorded_at", desc=True)
        .limit(1)
        .execute()
    )
    genome_row = genome_res.data[0] if genome_res.data else None

    proximity_res = (
        client.table("network_proximity_scores").select("*").eq("founder_id", founder_id).limit(1).execute()
    )
    proximity_row = proximity_res.data[0] if proximity_res.data else None

    return {
        "id": founder["id"],
        "display_name": founder["display_name"],
        "founder_score": history[-1]["score"] if history else None,
        "founder_score_trend": _score_trend(history),
        "genome": {
            dim: _genome_dimension(genome_row, dim)
            for dim in [
                "execution_velocity",
                "technical_depth",
                "resilience_proxy",
                "public_footprint_depth",
                "network_embeddedness",
            ]
        }
        if genome_row
        else None,
        "founder_score_history": history,
        "domain_affinity": founder.get("domain_affinity") or [],
        "network_proximity": {
            "proximity_score": proximity_row["proximity_score"],
            "confidence": proximity_row["confidence"],
            "disclosure": proximity_row.get("disclosure") or DISCLOSURE_TEXT,
        }
        if proximity_row
        else None,
    }


def get_network_graph(founder_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        return None  # frontend falls back to its local fixture directly

    center_res = (
        client.table("network_nodes").select("id").eq("ref_founder_id", founder_id).limit(1).execute()
    )
    if not center_res.data:
        return None
    center_node_id = center_res.data[0]["id"]

    def _neighbors(node_ids: set[str]) -> list[dict[str, Any]]:
        edges = (
            client.table("network_edges")
            .select("*")
            .or_(f"from_node_id.in.({','.join(node_ids)}),to_node_id.in.({','.join(node_ids)})")
            .execute()
        )
        return edges.data or []

    hop1_edges = _neighbors({center_node_id})
    frontier = {center_node_id}
    for e in hop1_edges:
        frontier.add(e["from_node_id"])
        frontier.add(e["to_node_id"])

    hop2_edges = _neighbors(frontier) if len(frontier) > 1 else []
    all_edges = {e["id"]: e for e in (hop1_edges + hop2_edges)}.values()

    node_ids: set[str] = {center_node_id}
    for e in all_edges:
        node_ids.add(e["from_node_id"])
        node_ids.add(e["to_node_id"])

    nodes_res = client.table("network_nodes").select("*").in_("id", list(node_ids)).execute()
    node_rows = {n["id"]: n for n in nodes_res.data}

    # Prefer the founder's own stable id as the graph node id (so the UI's
    # "is this the center node" check `n.id === founderId` works), otherwise
    # keep the raw network_nodes row id.
    display_id = {
        nid: (row.get("ref_founder_id") or nid) for nid, row in node_rows.items()
    }

    founder_network = {
        "nodes": [
            {
                "id": display_id[nid],
                "type": row["type"],
                "label": row["label"],
                "confidence": row.get("confidence"),
                "tags": row.get("tags") or [],
            }
            for nid, row in node_rows.items()
        ],
        "edges": [
            {
                "from": display_id.get(e["from_node_id"], e["from_node_id"]),
                "to": display_id.get(e["to_node_id"], e["to_node_id"]),
                "relationType": e["relation_type"],
                "weight": e.get("weight"),
                "firstSeenAt": e.get("first_seen_at"),
            }
            for e in all_edges
        ],
    }

    proximity_res = (
        client.table("network_proximity_scores").select("*").eq("founder_id", founder_id).limit(1).execute()
    )
    proximity_row = proximity_res.data[0] if proximity_res.data else None

    return {
        "founderId": founder_id,
        "founderNetwork": founder_network,
        "networkProximity": {
            "proximityScore": proximity_row["proximity_score"],
            "confidence": proximity_row["confidence"],
            "disclosure": proximity_row.get("disclosure") or DISCLOSURE_TEXT,
            "paths": [],
        }
        if proximity_row
        else None,
    }
