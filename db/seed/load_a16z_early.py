#!/usr/bin/env python3
"""Replace demo/fake companies with 10 early-stage a16z portfolio companies.

Source list curated from https://a16z.com/portfolio/ and
https://a16z.com/investment-list/ (public investment disclosures).
Company websites + LinkedIn company pages are public URLs.

Usage:
  cd apps/api && ../.venv/bin/python ../../db/seed/load_a16z_early.py
  # or from repo root with PYTHONPATH=apps/api
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from api.core.db import get_client  # noqa: E402
from api.core import opportunity_store  # noqa: E402
from api.ingestion import memory  # noqa: E402

MANIFEST = Path(__file__).resolve().parent / "a16z_early_stage.json"

# Synthetic / fixture names to purge (case-insensitive exact match)
FAKE_COMPANY_NAMES = {
    "latticeforge",
    "orbitstack",
    "felix",
    "atlas",
    "chainvault",
    "datapulse",
    "kerneldb",
    "lee analytics",
    "novametrics",
    "rivera labs",
    "trial",
    "amazon",
    "tower",
    "zepto",
    "zamp",
    "cispa european cybersecurity & ai hackathon",
    "bluzar",
    "instalily ai",
    "mbodi ai",
    "polymath",
    "veris ai",
    "openai",
}


def _purge(client) -> None:
    """Delete fake/demo + non-a16z *outbound* only. Never touch inbound applications."""
    opps = (
        client.table("opportunities")
        .select("id, source, company_id, founder_id, companies(name)")
        .execute()
        .data
    )
    delete_opp_ids = []
    company_ids = set()
    founder_ids = set()
    for o in opps:
        # Inbound decks (awesome-pitch-decks etc.) must stay
        if (o.get("source") or "").strip().lower() == "inbound":
            continue
        name = ((o.get("companies") or {}).get("name") or "").strip().lower()
        # Outbound: remove fakes, or prior outbound rows we're about to replace
        if name in FAKE_COMPANY_NAMES or (o.get("source") or "").strip().lower() == "outbound":
            delete_opp_ids.append(o["id"])
            if o.get("company_id"):
                company_ids.add(o["company_id"])
            if o.get("founder_id"):
                founder_ids.add(o["founder_id"])

    for oid in delete_opp_ids:
        client.table("opportunities").delete().eq("id", oid).execute()
    print(f"deleted {len(delete_opp_ids)} outbound/demo opportunities (inbound preserved)")

    # Only delete companies that are no longer referenced by any opportunity
    for cid in company_ids:
        still = client.table("opportunities").select("id").eq("company_id", cid).limit(1).execute().data
        if still:
            continue
        name_row = client.table("companies").select("name").eq("id", cid).limit(1).execute().data
        cname = (name_row[0].get("name") if name_row else "") or ""
        for table, col in (
            ("founder_company_roles", "company_id"),
            ("network_nodes", "ref_company_id"),
            ("wayback_snapshots", "company_id"),
            ("wayback_narratives", "company_id"),
        ):
            try:
                client.table(table).delete().eq(col, cid).execute()
            except Exception:
                pass
        try:
            client.table("network_nodes").update({"ref_company_id": None}).eq("ref_company_id", cid).execute()
        except Exception:
            pass
        try:
            client.table("companies").delete().eq("id", cid).execute()
        except Exception as exc:  # noqa: BLE001
            print(f"  skip company delete {cname}: {exc}")
    print("orphan outbound companies cleaned")

    for fid in founder_ids:
        still = client.table("opportunities").select("id").eq("founder_id", fid).limit(1).execute().data
        if not still:
            try:
                client.table("network_nodes").update({"ref_founder_id": None}).eq("ref_founder_id", fid).execute()
            except Exception:
                pass
            try:
                client.table("founders").delete().eq("id", fid).execute()
            except Exception as exc:  # noqa: BLE001
                print(f"  keep founder {fid}: {exc}")


def _seed(client, items: list[dict]) -> None:
    for item in items:
        company = memory.resolve_company(
            item["company_name"],
            domain=item.get("domain"),
            sector=item.get("sector"),
            source="a16z-portfolio",
        )
        client.table("companies").update({
            "domain": item.get("domain"),
            "sector": item.get("sector"),
            "stage": item.get("stage"),
            "description": item.get("a16z_note"),
            "source": "a16z-portfolio",
            "source_entity_id": item.get("domain"),
            "enrichment": {
                "website": item.get("website"),
                "linkedin_url": item.get("linkedin_url"),
                "a16z": True,
                "disclaimer": (
                    "Company listed on a16z public portfolio / investment list "
                    "(https://a16z.com/portfolio/, https://a16z.com/investment-list/). "
                    "Not representative of all a16z investments."
                ),
                "sources": ["a16z-portfolio"],
            },
        }).eq("id", company["id"]).execute()

        founder = memory.resolve_founder(
            item["founder_name"],
            source="a16z-portfolio",
            source_entity_id=item.get("linkedin_url") or item.get("domain"),
        )

        # Link role if missing
        roles = (
            client.table("founder_company_roles")
            .select("id")
            .eq("founder_id", founder["id"])
            .eq("company_id", company["id"])
            .limit(1)
            .execute()
            .data
        )
        if not roles:
            client.table("founder_company_roles").insert({
                "founder_id": founder["id"],
                "company_id": company["id"],
                "role": "cofounder",
            }).execute()

        channels = "perplexity,web_search,linkedin"
        opp = opportunity_store.create_opportunity(
            company_name=item["company_name"],
            founder_name=item["founder_name"],
            source="outbound",
            discovery_channel=channels,
            triggering_signal=(
                f"a16z portfolio company · {item.get('website')} · {item.get('linkedin_url')}"
            ),
            force_new=True,
        )
        opportunity_store.update_opportunity(
            opp["id"],
            screen_verdict="pass",
            status="screening",
            thesis_fit_score=0.72,
        )
        opportunity_store.set_sla_stage(opp["id"], "screening_at")
        print(f"  + {item['company_name']} → opp {opp['id'][:8]}…  {item.get('website')}")


def main() -> int:
    client = get_client()
    if client is None:
        print("Supabase not configured", file=sys.stderr)
        return 1
    items = json.loads(MANIFEST.read_text())
    print(f"Purging demo data, then loading {len(items)} early-stage a16z companies…")
    _purge(client)
    _seed(client, items)
    print("Done. Attribution: https://a16z.com/portfolio/ · https://a16z.com/investment-list/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
