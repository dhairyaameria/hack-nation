"""Founder profile + network graph reads — backed by `founders`,
`founder_genome_snapshots`, `founder_score_history`,
`network_proximity_scores`, `network_nodes`/`network_edges`.

Falls back to `shared/fixtures/founder-profile.json` /
`network-graph-seed.json` when Supabase isn't configured, so the UI still
demos without credentials (see `docs/15-MOCK-FIXTURES.md`).
"""

from __future__ import annotations

from typing import Any

from api.core import fixtures, gold_features
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


def _genome_from_gold(gold: dict[str, Any]) -> dict[str, Any]:
    return {
        dim: {
            "value": gold.get(dim),
            "trend": "stable",
            "confidence": gold.get("confidence"),
            "evidence": [],
        }
        for dim in [
            "execution_velocity",
            "technical_depth",
            "resilience_proxy",
            "public_footprint_depth",
            "network_embeddedness",
        ]
    }


def list_founders(*, limit: int = 100) -> list[dict[str, Any]]:
    """Founder Book index — scores + company when known."""
    client = get_client()
    if client is None:
        fixture = fixtures.get_founder_profile("founder-a-cold-start-strong")
        if not fixture:
            return []
        return [{
            "id": fixture["id"],
            "display_name": fixture["display_name"],
            "founder_score": fixture.get("founder_score"),
            "founder_score_trend": fixture.get("founder_score_trend"),
            "company_name": None,
            "source": None,
            "has_enrichment": False,
        }]

    try:
        founders_res = (
            client.table("founders")
            .select("id, display_name, source, enrichment, created_at")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception:
        # Migration 013 not applied — list without enrichment column.
        founders_res = (
            client.table("founders")
            .select("id, display_name, source, created_at")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
    rows = founders_res.data or []
    if not rows:
        return []

    ids = [r["id"] for r in rows]
    history_res = (
        client.table("founder_score_history")
        .select("founder_id, score, recorded_at")
        .in_("founder_id", ids)
        .order("recorded_at", desc=True)
        .execute()
    )
    latest_score: dict[str, float] = {}
    for h in history_res.data or []:
        fid = h["founder_id"]
        if fid not in latest_score:
            latest_score[fid] = h["score"]

    company_by_founder: dict[str, str] = {}
    source_by_founder: dict[str, str] = {}
    opp_res = (
        client.table("opportunities")
        .select("founder_id, source, companies(name)")
        .in_("founder_id", ids)
        .execute()
    )
    for o in opp_res.data or []:
        fid = o["founder_id"]
        companies = o.get("companies")
        if fid not in company_by_founder and isinstance(companies, dict) and companies.get("name"):
            company_by_founder[fid] = companies["name"]
        if fid not in source_by_founder and o.get("source"):
            source_by_founder[fid] = o["source"]

    wl_res = (
        client.table("watchlist_entries")
        .select("founder_id, companies(name)")
        .in_("founder_id", ids)
        .execute()
    )
    for w in wl_res.data or []:
        fid = w["founder_id"]
        companies = w.get("companies")
        if fid not in company_by_founder and isinstance(companies, dict) and companies.get("name"):
            company_by_founder[fid] = companies["name"]
        if fid not in source_by_founder:
            source_by_founder[fid] = "outbound"

    out: list[dict[str, Any]] = []
    for r in rows:
        fid = r["id"]
        enrich = r.get("enrichment") or {}
        out.append({
            "id": fid,
            "display_name": r["display_name"],
            # List stays fast — score comes from history only (profile/enrich fills it).
            "founder_score": latest_score.get(fid),
            "founder_score_trend": None,
            "company_name": company_by_founder.get(fid),
            "source": source_by_founder.get(fid) or r.get("source"),
            "has_enrichment": bool(enrich.get("summary")),
        })

    # Scored founders first (highest score), then unscored by recency (input order).
    out.sort(
        key=lambda f: (
            0 if f.get("founder_score") is not None else 1,
            -(f["founder_score"] if f.get("founder_score") is not None else 0),
        )
    )
    return out


def get_founder_profile(founder_id: str, *, enrich: bool = False) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        return fixtures.get_founder_profile(founder_id)

    if enrich:
        try:
            from api.ingestion import founder_enrich

            founder_enrich.get_or_enrich_founder(founder_id, force=False)
        except KeyError:
            return None
        except Exception as exc:  # noqa: BLE001 — profile still loads without live research
            print(f"[founder_store] enrich skipped: {exc}")

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

    gold = None
    if not genome_row or not history:
        gold = gold_features.get_gold_features(founder_id)
        if gold and not genome_row:
            gold_features.upsert_genome_snapshot(founder_id, gold)
            genome_row = {
                **{k: gold.get(k) for k in (
                    "execution_velocity",
                    "technical_depth",
                    "resilience_proxy",
                    "public_footprint_depth",
                    "network_embeddedness",
                )},
                "confidence": gold.get("confidence"),
            }
        if gold and not history:
            score = gold_features.compute_founder_score(gold)
            gold_features.append_score_history(founder_id, score, gold.get("confidence") or 0.4)
            history = [{"recorded_at": gold_features._today_midnight_iso(), "score": score}]

    proximity_res = (
        client.table("network_proximity_scores").select("*").eq("founder_id", founder_id).limit(1).execute()
    )
    proximity_row = proximity_res.data[0] if proximity_res.data else None

    founder_score = history[-1]["score"] if history else None
    if founder_score is None and gold:
        founder_score = gold_features.compute_founder_score(gold)

    genome = None
    if genome_row:
        genome = {
            dim: _genome_dimension(genome_row, dim)
            for dim in [
                "execution_velocity",
                "technical_depth",
                "resilience_proxy",
                "public_footprint_depth",
                "network_embeddedness",
            ]
        }
    elif gold:
        genome = _genome_from_gold(gold)

    enrichment = founder.get("enrichment") or {}
    if not enrichment.get("summary"):
        from api.ingestion.founder_enrich import enrichment_from_bronze

        enrichment = enrichment_from_bronze(client, founder) or enrichment

    return {
        "id": founder["id"],
        "display_name": founder["display_name"],
        "location": founder.get("location"),
        "founder_score": founder_score,
        "founder_score_trend": _score_trend(history),
        "genome": genome,
        "founder_score_history": history,
        "domain_affinity": founder.get("domain_affinity") or [],
        "enrichment": enrichment,
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
