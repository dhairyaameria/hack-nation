#!/usr/bin/env python3
"""Restore inbound awesome-pitch-deck applications (no HTTP API required).

Downloads PDFs from the manifest Drive links and creates source=inbound
opportunities with decks in Supabase Storage — same outcome as
POST /application/submit.

Usage:
  cd apps/api && .venv/bin/python ../../db/seed/restore_inbound_awesome.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from api.core.db import get_client  # noqa: E402
from api.core import opportunity_store  # noqa: E402
from api.ingestion import deck_parser, deck_storage, deck_store, fast_screen  # noqa: E402

MANIFEST = Path(__file__).resolve().parent / "awesome_decks_manifest.json"
CACHE = Path(__file__).resolve().parent / "decks"


def drive_download_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def download_pdf(file_id: str, dest: Path) -> bytes:
    if dest.is_file() and dest.stat().st_size > 1000:
        data = dest.read_bytes()
        if data[:4] == b"%PDF":
            return data
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=90) as client:
        r = client.get(drive_download_url(file_id))
        if "text/html" in r.headers.get("content-type", "") and "confirm=" in r.text:
            import re

            m = re.search(r"confirm=([0-9A-Za-z_]+)", r.text)
            if m:
                r = client.get(
                    f"https://drive.google.com/uc?export=download&confirm={m.group(1)}&id={file_id}"
                )
        r.raise_for_status()
        data = r.content
        if len(data) < 500 or data[:4] != b"%PDF":
            raise RuntimeError(f"Download for {file_id} did not look like a PDF ({len(data)} bytes)")
        dest.write_bytes(data)
        return data


def already_inbound(client, company_name: str) -> bool:
    rows = (
        client.table("opportunities")
        .select("id, companies(name)")
        .eq("source", "inbound")
        .execute()
        .data
    )
    target = company_name.strip().lower()
    for o in rows:
        name = ((o.get("companies") or {}).get("name") or "").strip().lower()
        if name == target:
            return True
    return False


def restore_one(company: str, founder: str, pdf: bytes, filename: str) -> dict:
    claims = deck_parser.parse_deck(pdf)
    verdict, _reason = fast_screen.screen(company, claims)
    opp = opportunity_store.create_opportunity(
        company_name=company,
        founder_name=founder,
        source="inbound",
        discovery_channel="direct_apply",
    )
    deck_meta = deck_storage.upload_deck(opp["id"], pdf, filename)
    local_meta = deck_store.save_deck(opp["id"], pdf, filename)
    if not deck_meta.get("deck_storage_path"):
        deck_meta["deck_storage_path"] = local_meta["deck_storage_path"]
    if not deck_meta.get("deck_filename"):
        deck_meta["deck_filename"] = local_meta["deck_filename"]
    if not deck_meta.get("deck_url"):
        deck_meta["deck_url"] = f"/api/v1/inbound/applications/{opp['id']}/deck"

    opportunity_store.update_opportunity(
        opp["id"],
        claims=[{**c, "claim_id": f"claim-{i}"} for i, c in enumerate(claims)],
        screen_verdict=verdict,
        status="screening" if verdict == "pass" else "rejected" if verdict == "reject" else "needs-more-info",
        **deck_meta,
    )
    opportunity_store.set_sla_stage(opp["id"], "screening_at")
    return {
        "opportunity_id": opp["id"],
        "claims": len(claims),
        "verdict": verdict,
    }


def main() -> int:
    client = get_client()
    if client is None:
        print("Supabase not configured", file=sys.stderr)
        return 1

    items = json.loads(MANIFEST.read_text())
    print(f"Restoring {len(items)} inbound awesome-pitch-deck applications…")
    ok = 0
    for item in items:
        company = item["company_name"]
        founder = item["founder_name"]
        if already_inbound(client, company):
            print(f"  skip {company} (already inbound)")
            ok += 1
            continue
        file_id = item["drive_file_id"]
        filename = f"{company.replace(' ', '_')}-{item.get('year', '')}-{item.get('round', 'Seed')}.pdf"
        dest = CACHE / filename
        print(f"→ {company} …", flush=True)
        try:
            pdf = download_pdf(file_id, dest)
            result = restore_one(company, founder, pdf, filename)
            print(
                f"  ok opp={result['opportunity_id'][:8]}… "
                f"claims={result['claims']} verdict={result['verdict']}"
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL: {exc}", file=sys.stderr)
    print(f"Done — {ok}/{len(items)} inbound applications present.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
