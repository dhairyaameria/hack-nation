#!/usr/bin/env python3
"""Load `shared/fixtures/real-cast.json` into Supabase as founders, companies,
opportunities (status=screening), Bronze-ish notes on companies, and a network
subgraph.

Does NOT invent traction claims. Opportunities start with zero deck claims so
Analyze / memo generation must research from public signals or gap-flag.

Usage:

    python db/seed/load_real_cast.py
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

CAST_PATH = REPO_ROOT / "shared" / "fixtures" / "real-cast.json"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SLUG_NAMESPACE = uuid.UUID("8f14e45f-ceea-4bad-b7bc-6a4c8b7c6a3e")


def sid(slug: str) -> str:
    return str(uuid.uuid5(SLUG_NAMESPACE, slug))


def upsert(client, table: str, rows: list[dict], on_conflict: str = "id"):
    if not rows:
        return
    client.table(table).upsert(rows, on_conflict=on_conflict).execute()
    print(f"  upserted {len(rows)} → {table}")


def main() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Missing SUPABASE_URL / SUPABASE_SERVICE_KEY")
        sys.exit(1)
    if not CAST_PATH.exists():
        print(f"Missing {CAST_PATH} — run: python db/seed/harvest_real_cast.py")
        sys.exit(1)

    from supabase import create_client

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    cast = json.loads(CAST_PATH.read_text())
    people = cast["people"]
    network = cast.get("network") or {"nodes": [], "edges": []}
    thesis_id = sid("thesis-ai-infra-eu")

    print(f"Loading real cast v{cast.get('version')} ({len(people)} people)...")

    founder_rows = []
    company_rows = []
    opp_rows = []
    bronze_rows = []

    for p in people:
        fid = sid(p["slug"])
        founder_rows.append({
            "id": fid,
            "display_name": p["display_name"],
            "domain_affinity": (
                [{"sector": p["sector"], "weight": 0.7, "confidence": 0.55, "evidence_source": "linkedin_public"}]
                if p.get("sector")
                else []
            ),
            "source_entity_id": p.get("github_username") or p.get("linkedin_slug"),
        })

        company_name = p.get("company_name")
        if company_name:
            cslug = "company-" + company_name.lower().replace(" ", "-").replace(".", "")[:40]
            cid = sid(cslug)
            company_rows.append({
                "id": cid,
                "name": company_name,
                "domain": p.get("company_domain"),
                "sector": p.get("sector") or "ai_infra",
                "status": "active",
            })
            opp_rows.append({
                "id": sid(f"opp-{p['slug']}"),
                "founder_id": fid,
                "company_id": cid,
                "thesis_profile_id": thesis_id,
                "source": "outbound",
                "discovery_channel": "linkedin",
                "triggering_signal": (
                    f"Real-cast harvest · LinkedIn {p.get('linkedin_slug')} · "
                    f"identity={p.get('identity_confidence')}"
                ),
                "screen_verdict": "pass",
                "thesis_fit_score": 0.7 if p.get("sector") == "ai_infra" else 0.45,
                "status": "screening",
                "has_contradiction": False,
            })

        # Bronze provenance snapshot (payload only — no fabricated claims)
        bronze_rows.append({
            "id": sid(f"bronze-{p['slug']}"),
            "source": "linkedin",
            "entity_type": "founder_profile",
            "source_entity_id": p.get("linkedin_slug") or p["slug"],
            "payload": {
                "display_name": p["display_name"],
                "linkedin_url": p["linkedin_url"],
                "company_name": company_name,
                "github_username": p.get("github_username"),
                "identity_confidence": p.get("identity_confidence"),
                "signals": {
                    k: v
                    for k, v in (p.get("signals") or {}).items()
                    if k in ("linkedin", "github", "hackernews", "arxiv") and v
                },
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

    print("1. Founders")
    upsert(client, "founders", founder_rows)
    print("2. Companies")
    upsert(client, "companies", company_rows)
    print("3. Opportunities")
    upsert(client, "opportunities", opp_rows)
    print("4. Bronze raw events")
    try:
        upsert(client, "bronze_raw_events", bronze_rows)
    except Exception as exc:  # noqa: BLE001
        print(f"  bronze skip ({exc})")

    print("5. Network nodes / edges")
    node_rows = []
    for n in network.get("nodes", []):
        row = {
            "id": sid(n["slug"]),
            "type": n["type"],
            "label": n["label"],
            "confidence": n.get("confidence", 0.7),
            "tags": n.get("tags") or [],
        }
        if n["slug"].startswith("founder-"):
            row["ref_founder_id"] = sid(n["slug"])
        if n["slug"].startswith("company-"):
            row["ref_company_id"] = sid(n["slug"])
        node_rows.append(row)
    upsert(client, "network_nodes", node_rows)

    edge_rows = [
        {
            "from_node_id": sid(e["from"]),
            "to_node_id": sid(e["to"]),
            "relation_type": e["relation_type"],
            "weight": e.get("weight", 0.5),
            "first_seen_at": e.get("first_seen_at") or datetime.now(timezone.utc).date().isoformat(),
        }
        for e in network.get("edges", [])
    ]
    try:
        upsert(client, "network_edges", edge_rows, on_conflict="from_node_id,to_node_id,relation_type")
    except Exception as exc:  # noqa: BLE001
        print(f"  edges upsert soft-fail ({exc}); trying insert-ignore loop")
        for row in edge_rows:
            try:
                client.table("network_edges").upsert(row, on_conflict="from_node_id,to_node_id,relation_type").execute()
            except Exception:
                pass

    print("Done.")
    print("Next: set NEXT_PUBLIC_USE_FIXTURES=false and refresh Outbound / Founder Book.")
    print("Open opportunities and run Analyze — memos should gap-flag missing traction.")


if __name__ == "__main__":
    main()
