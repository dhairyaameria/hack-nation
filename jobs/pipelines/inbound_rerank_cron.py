#!/usr/bin/env python3
"""Cron / scheduler entrypoint for inbound Perplexity rerank.

Runs the SAME function as `POST /api/v1/inbound/rerank` — no UI coupling.

Usage (from repo root, with API venv + .env loaded):

    cd apps/api && source .venv/bin/activate
    PYTHONPATH=. python ../../jobs/pipelines/inbound_rerank_cron.py

Or via Makefile:

    make inbound-rerank

Example crontab (hourly):

    0 * * * * cd /path/to/hack-nation && make inbound-rerank >> /tmp/inbound-rerank.log 2>&1

See docs/19-INBOUND-RERANK.md for cost / scale notes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `from api...` when launched as a script from repo root or apps/api.
API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from api.ingestion.inbound_rerank import rerank_inbound  # noqa: E402


def main() -> int:
    result = rerank_inbound(trigger="cron")
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
