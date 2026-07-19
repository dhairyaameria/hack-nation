#!/usr/bin/env python3
"""Download Pre-Seed/Seed decks from awesome-pitch-decks Drive links and
submit them through the inbound application API.

Usage (API must be running):
  python db/seed/load_awesome_decks.py
  python db/seed/load_awesome_decks.py --api http://localhost:8000 --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).resolve().parent / "awesome_decks_manifest.json"
CACHE = Path(__file__).resolve().parent / "decks"


def drive_download_url(file_id: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def download_pdf(file_id: str, dest: Path) -> bytes:
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest.read_bytes()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        # Google sometimes returns an HTML interstitial for large files
        r = client.get(drive_download_url(file_id))
        if "text/html" in r.headers.get("content-type", "") and "confirm=" in r.text:
            # retry with confirm token if present
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


def submit(api: str, company: str, founder: str, pdf: bytes, filename: str) -> dict:
    with httpx.Client(timeout=120) as client:
        r = client.post(
            f"{api.rstrip('/')}/api/v1/application/submit",
            data={"company_name": company, "founder_name": founder},
            files={"deck": (filename, pdf, "application/pdf")},
        )
        r.raise_for_status()
        return r.json()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--limit", type=int, default=0, help="0 = all in manifest")
    parser.add_argument("--skip-download-errors", action="store_true")
    args = parser.parse_args()

    items = json.loads(MANIFEST.read_text())
    if args.limit:
        items = items[: args.limit]

    ok = 0
    for item in items:
        company = item["company_name"]
        founder = item["founder_name"]
        file_id = item["drive_file_id"]
        filename = f"{company.replace(' ', '_')}-{item.get('year', '')}-{item.get('round', 'Seed')}.pdf"
        dest = CACHE / filename
        print(f"→ {company} ({item.get('round')}) …", flush=True)
        try:
            pdf = download_pdf(file_id, dest)
            result = submit(args.api, company, founder, pdf, filename)
            print(
                f"  ok opportunity={result.get('opportunity_id')} "
                f"company={result.get('company_id')} claims={result.get('claims_extracted')} "
                f"verdict={result.get('screen_verdict')}"
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL: {exc}", file=sys.stderr)
            if not args.skip_download_errors:
                return 1
    print(f"Done — {ok}/{len(items)} applications loaded.")
    print("Attribution: PDFs indexed by midovislam/awesome-pitch-decks (rights remain with companies).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
