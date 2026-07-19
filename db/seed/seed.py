#!/usr/bin/env python3
"""Idempotent demo seed script — loads the full cast from
`docs/14-SEED-DATA-SPEC.md` into Supabase.

Slugs (e.g. "founder-a-cold-start-strong") are deterministically mapped to
UUIDs via uuid5, so re-running this script upserts the same rows instead of
duplicating them. Run with:

    python db/seed/seed.py

Requires SUPABASE_URL + SUPABASE_SERVICE_KEY in the root `.env` (or
environment). Safe to re-run — every insert is an upsert on a stable id.
"""

from __future__ import annotations

import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Fixed namespace so slug -> UUID mapping never drifts between runs/agents.
SLUG_NAMESPACE = uuid.UUID("8f14e45f-ceea-4bad-b7bc-6a4c8b7c6a3e")


def sid(slug: str) -> str:
    """Stable UUID for a human-readable seed slug."""
    return str(uuid.uuid5(SLUG_NAMESPACE, slug))


def iso(dt: datetime) -> str:
    return dt.isoformat()


NOW = datetime.now(timezone.utc)


def days_ago(n: int) -> datetime:
    return NOW - timedelta(days=n)


# ---------------------------------------------------------------------------
# 1. Thesis profiles — docs/12-THESIS-SETTINGS-UI.md §6
# ---------------------------------------------------------------------------

THESES = [
    {
        "id": sid("thesis-ai-infra-eu"),
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
    },
    {
        "id": sid("thesis-devtools-us"),
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
    },
]

# ---------------------------------------------------------------------------
# 2. Founders — docs/14-SEED-DATA-SPEC.md §2
# ---------------------------------------------------------------------------

FOUNDER_SLUGS = {
    "founder-a-cold-start-strong": "Alex Rivera",
    "founder-b-network-heavy-weak": "Jordan Lee",
    "founder-contradiction": "Elena Vasquez",
    "founder-wayback-resilience": "Sam Okonkwo",
    "founder-established": "Priya Nair",
    "founder-established-2": "Marcus Chen",
    "founder-cold-public-only": "Lina Hoffmann",
    "founder-cold-network-only": "Tomás Ruiz",
    "founder-outbound-signal": "Aisha Khan",
    "founder-excluded-sector": "Nikolai Petrov",
    "founder-portfolio-lattice": "Maya Okonkwo",
    "founder-portfolio-orbit": "Jonas Berg",
}

DOMAIN_AFFINITY = {
    "founder-wayback-resilience": [
        {"sector": "b2b_saas", "weight": 0.7, "confidence": 0.7, "evidence_source": "wayback"},
        {"sector": "analytics", "weight": 0.5, "confidence": 0.6, "evidence_source": "role_history"},
    ],
    "founder-established": [
        {"sector": "ai_infra", "weight": 0.85, "confidence": 0.8, "evidence_source": "role_history"},
    ],
    "founder-established-2": [
        {"sector": "devtools", "weight": 0.9, "confidence": 0.85, "evidence_source": "github"},
    ],
}

FOUNDERS = [
    {"id": sid(slug), "display_name": name, "slug": slug}
    for slug, name in FOUNDER_SLUGS.items()
]
for f in FOUNDERS:
    f["domain_affinity"] = DOMAIN_AFFINITY.get(f["slug"], [])

# Genome snapshots — bias-test pair values from docs/14-SEED-DATA-SPEC.md §2
GENOME_TARGETS = {
    "founder-a-cold-start-strong": (0.88, 0.82, 0.75, 0.70, 0.08),
    "founder-b-network-heavy-weak": (0.35, 0.40, 0.45, 0.50, 0.72),
    "founder-contradiction": (0.72, 0.68, 0.60, 0.65, 0.25),
    "founder-wayback-resilience": (0.65, 0.70, 0.80, 0.55, 0.30),
}

FOUNDER_SCORE_HISTORY = {
    "founder-a-cold-start-strong": [0.62, 0.71, 0.78],
    "founder-b-network-heavy-weak": [0.38, 0.40, 0.41],
}

# ---------------------------------------------------------------------------
# 3. Companies — docs/14-SEED-DATA-SPEC.md §3
# ---------------------------------------------------------------------------

COMPANIES = [
    {"slug": "company-a", "name": "Rivera Labs", "domain": "riveralabs.dev", "sector": "ai_infra", "status": "active"},
    {"slug": "company-b", "name": "Lee Analytics", "domain": "leeanalytics.io", "sector": "analytics", "status": "active"},
    {"slug": "company-novametrics", "name": "NovaMetrics", "domain": "novametrics.ai", "sector": "ai_infra", "status": "active"},
    {"slug": "company-datapulse", "name": "DataPulse", "domain": "datapulse.io", "sector": "b2b_saas", "status": "dead"},
    {"slug": "company-outbound", "name": "KernelDB", "domain": "kerneldb.io", "sector": "devtools", "status": "active"},
    {"slug": "company-crypto", "name": "ChainVault", "domain": "chainvault.xyz", "sector": "crypto", "status": "active"},
    {"slug": "company-latticeforge", "name": "LatticeForge", "domain": "latticeforge.ai", "sector": "ai_infra", "status": "active"},
    {"slug": "company-orbitstack", "name": "OrbitStack", "domain": "orbitstack.dev", "sector": "devtools", "status": "active"},
]

# ---------------------------------------------------------------------------
# 4. Opportunities — docs/14-SEED-DATA-SPEC.md §4
# ---------------------------------------------------------------------------

OPPORTUNITIES = [
    {"slug": "opp-alex-inbound", "founder": "founder-a-cold-start-strong", "company": "company-a",
     "source": "inbound", "discovery_channel": "direct_apply", "screen_verdict": "pass",
     "thesis_fit_score": 0.91, "status": "screening"},
    {"slug": "opp-jordan-outbound", "founder": "founder-b-network-heavy-weak", "company": "company-b",
     "source": "outbound", "discovery_channel": "network_proximity",
     "triggering_signal": "2-hop path to Sequoia via co-author", "screen_verdict": "pass",
     "thesis_fit_score": 0.58, "status": "screening"},
    {"slug": "opp-contradiction", "founder": "founder-contradiction", "company": "company-novametrics",
     "source": "inbound", "discovery_channel": "direct_apply", "screen_verdict": "pass",
     "thesis_fit_score": 0.79, "status": "diligence", "has_contradiction": True},
    {"slug": "opp-wayback", "founder": "founder-wayback-resilience", "company": "company-datapulse",
     "source": "inbound", "discovery_channel": "direct_apply", "screen_verdict": "pass",
     "thesis_fit_score": 0.66, "status": "screening"},
    {"slug": "opp-outbound-hn", "founder": "founder-outbound-signal", "company": "company-outbound",
     "source": "outbound", "discovery_channel": "hacker_news", "screen_verdict": "pass",
     "thesis_fit_score": 0.70, "status": "screening"},
    {"slug": "opp-crypto-excluded", "founder": "founder-excluded-sector", "company": "company-crypto",
     "source": "inbound", "discovery_channel": "direct_apply", "screen_verdict": "reject",
     "thesis_fit_score": 0.12, "status": "rejected"},
    {"slug": "opp-portfolio-lattice", "founder": "founder-portfolio-lattice", "company": "company-latticeforge",
     "source": "outbound", "discovery_channel": "github", "screen_verdict": "pass",
     "thesis_fit_score": 0.88, "status": "funded", "funded_days_ago": 47,
     "triggering_signal": "Strong public shipping cadence on GPU kernel tooling"},
    {"slug": "opp-portfolio-orbit", "founder": "founder-portfolio-orbit", "company": "company-orbitstack",
     "source": "inbound", "discovery_channel": "direct_apply", "screen_verdict": "pass",
     "thesis_fit_score": 0.81, "status": "funded", "funded_days_ago": 118},
]

# ---------------------------------------------------------------------------
# 5. Seeded contradiction — docs/14-SEED-DATA-SPEC.md §5
# ---------------------------------------------------------------------------

CONTRADICTION_CLAIMS = [
    {
        "slug": "claim-arr-500k",
        "text": "We are at $500K ARR",
        "slide_locator": "slide 8",
        "contradicting_evidence": {
            "source_type": "web",
            "source_locator": "https://producthunt.com/posts/novametrics",
            "evidence_snippet": "Pre-revenue — 12 design partners",
            "confidence": 0.88,
        },
        "validation_status": "contradicted",
        "trust_score": 0.22,
    },
    {
        "slug": "claim-customers-40",
        "text": "40 paying enterprise customers",
        "slide_locator": "slide 9",
        "contradicting_evidence": {
            "source_type": "web",
            "source_locator": "https://linkedin.com/company/novametrics",
            "evidence_snippet": "3 pilot customers",
            "confidence": 0.75,
        },
        "validation_status": "weakly_supported",
        "trust_score": 0.35,
    },
]

# ---------------------------------------------------------------------------
# 6. Wayback seed — docs/14-SEED-DATA-SPEC.md §6
# ---------------------------------------------------------------------------

WAYBACK_SNAPSHOTS = [
    {"snapshot_at": "2019-06-01", "extracted_summary": "Consumer social analytics for influencers", "sentiment": "neutral"},
    {"snapshot_at": "2020-03-01", "extracted_summary": "Pivoting to B2B dashboard for SMBs", "sentiment": "mixed"},
    {"snapshot_at": "2021-01-01", "extracted_summary": "Sunsetting product — team exploring acqui-hire", "sentiment": "negative"},
]

# ---------------------------------------------------------------------------
# 7. Network graph — mirrors shared/fixtures/network-graph-seed.json
# ---------------------------------------------------------------------------

NETWORK_NODES = [
    {"slug": "founder-a-cold-start-strong", "type": "Founder", "label": "Alex Rivera", "confidence": 0.85, "tags": []},
    {"slug": "company-a", "type": "Company", "label": "Rivera Labs", "confidence": 0.9, "tags": []},
    {"slug": "founder-peer-1", "type": "Founder", "label": "Sam Okonkwo", "confidence": 0.7, "tags": []},
    {"slug": "founder-b-network-heavy-weak", "type": "Founder", "label": "Jordan Lee", "confidence": 0.6, "tags": []},
    {"slug": "founder-via-bob", "type": "Founder", "label": "Bob Chen", "confidence": 0.88, "tags": []},
    {"slug": "vc-sequoia", "type": "VC", "label": "Sequoia Capital", "confidence": 0.95, "tags": ["anchor", "tier1_vc"]},
    {"slug": "accel-yc", "type": "Accelerator", "label": "Y Combinator", "confidence": 0.95, "tags": ["anchor"]},
    {"slug": "company-b", "type": "Company", "label": "Lee Analytics", "confidence": 0.5, "tags": []},
    {"slug": "founder-collab", "type": "Founder", "label": "Mia Patel", "confidence": 0.72, "tags": []},
    {"slug": "inst-stanford", "type": "Institution", "label": "Stanford University", "confidence": 0.9, "tags": ["anchor"]},
    {"slug": "vc-a16z", "type": "VC", "label": "Andreessen Horowitz", "confidence": 0.9, "tags": ["anchor", "tier1_vc"]},
]

NETWORK_EDGES = [
    {"from": "founder-a-cold-start-strong", "to": "company-a", "relation_type": "CO_CONTRIBUTED", "weight": 0.9, "first_seen_at": "2025-03-01"},
    {"from": "founder-a-cold-start-strong", "to": "founder-peer-1", "relation_type": "CO_PARTICIPATED", "weight": 0.6, "first_seen_at": "2024-11-15"},
    {"from": "founder-b-network-heavy-weak", "to": "founder-via-bob", "relation_type": "CO_AUTHORED", "weight": 0.85, "first_seen_at": "2025-01-10"},
    {"from": "founder-via-bob", "to": "vc-sequoia", "relation_type": "ALUMNI_OF", "weight": 0.9, "first_seen_at": "2023-06-01"},
    {"from": "founder-b-network-heavy-weak", "to": "founder-collab", "relation_type": "CO_CONTRIBUTED", "weight": 0.7, "first_seen_at": "2024-08-20"},
    {"from": "founder-collab", "to": "accel-yc", "relation_type": "CO_PARTICIPATED", "weight": 0.8, "first_seen_at": "2024-01-05"},
    {"from": "founder-b-network-heavy-weak", "to": "company-b", "relation_type": "CO_CONTRIBUTED", "weight": 0.4, "first_seen_at": "2025-02-01"},
]

NETWORK_PROXIMITY = {
    "founder-a-cold-start-strong": {"proximity_score": 0.08, "confidence": 0.75, "path_count": 2},
    "founder-b-network-heavy-weak": {"proximity_score": 0.72, "confidence": 0.82, "path_count": 2},
    "founder-cold-network-only": {"proximity_score": 0.55, "confidence": 0.6, "path_count": 1},
}

DISCLOSURE_TEXT = (
    "Network proximity signal — reflects who this founder is connected to, "
    "not their own demonstrated capability. Shown for transparency, weighted conservatively."
)

# ---------------------------------------------------------------------------
# 8. Memory layer: documents, chunks, facts, aliases (migration 012)
# ---------------------------------------------------------------------------


def fake_embedding(slug: str, dim: int = 1536) -> list[float]:
    """Deterministic stand-in for text-embedding-3-small so the seed works
    offline (no OPENAI_API_KEY) and re-runs upsert identical rows. Real
    ingestion via /api/v1/memory/ingest writes real embeddings.
    """
    rng = random.Random(slug)
    return [round(rng.uniform(-1, 1), 6) for _ in range(dim)]


MEMORY_DOCUMENTS = [
    {
        "slug": "doc-rivera-deck-notes",
        "title": "Rivera Labs seed deck notes",
        "doc_type": "deck",
        "founder": "founder-a-cold-start-strong",
        "company": "company-a",
        "source_type": "deck",
        "source_locator": "rivera-labs-deck.pdf",
        "source_timestamp": "2026-07-08T10:00:00+00:00",
        "chunks": [
            "Rivera Labs builds GPU scheduling infrastructure for AI training workloads. "
            "The team claims 3 design partners running production jobs and a 40% cost "
            "reduction versus naive scheduling in internal benchmarks.",
            "Founding team: Alex Rivera (CEO, ex-infra at a large cloud provider) plus two "
            "founding engineers. Raising to expand the scheduler to multi-cloud and hire a "
            "developer relations lead.",
        ],
    },
    {
        "slug": "doc-alex-intro-call",
        "title": "Intro call notes: Alex Rivera",
        "doc_type": "note",
        "founder": "founder-a-cold-start-strong",
        "company": "company-a",
        "source_type": "note",
        "source_locator": "calls/2026-07-10-alex-rivera.md",
        "source_timestamp": "2026-07-10T16:30:00+00:00",
        "chunks": [
            "30-minute intro call with Alex Rivera. Alex confirmed the round size changed: "
            "originally planned as a $500K pre-seed, now raising a $1.5M seed after "
            "inbound interest. Committed to sending updated pilot metrics by end of July. "
            "We agreed to move Rivera Labs into screening.",
        ],
    },
]

# One invalidated fact (valid_until set) demonstrates bi-temporality: the
# round-size claim from the deck was superseded on the intro call.
MEMORY_FACTS = [
    {
        "slug": "fact-alex-actor",
        "fact_type": "actor",
        "subject": "Alex Rivera",
        "body": "Alex Rivera is the founder and CEO of Rivera Labs.",
        "payload": {"role": "CEO", "company": "Rivera Labs"},
        "document": "doc-rivera-deck-notes",
        "confidence": 0.9,
        "valid_from": "2026-07-08T10:00:00+00:00",
        "valid_until": None,
    },
    {
        "slug": "fact-raise-500k",
        "fact_type": "claim",
        "subject": "Rivera Labs",
        "body": "Rivera Labs is raising a $500K pre-seed round.",
        "payload": {"amount_usd": 500000, "round": "pre_seed"},
        "document": "doc-rivera-deck-notes",
        "confidence": 0.85,
        "valid_from": "2026-07-08T10:00:00+00:00",
        "valid_until": "2026-07-10T16:30:00+00:00",  # superseded on the intro call
    },
    {
        "slug": "fact-raise-1500k",
        "fact_type": "claim",
        "subject": "Rivera Labs",
        "body": "Rivera Labs is raising a $1.5M seed round.",
        "payload": {"amount_usd": 1500000, "round": "seed"},
        "document": "doc-alex-intro-call",
        "confidence": 0.9,
        "valid_from": "2026-07-10T16:30:00+00:00",
        "valid_until": None,
    },
    {
        "slug": "fact-alex-metrics-commitment",
        "fact_type": "commitment",
        "subject": "Alex Rivera",
        "body": "Alex Rivera committed to sending updated pilot metrics by end of July 2026.",
        "payload": {"due": "2026-07-31"},
        "document": "doc-alex-intro-call",
        "confidence": 0.8,
        "valid_from": "2026-07-10T16:30:00+00:00",
        "valid_until": None,
    },
    {
        "slug": "fact-screening-decision",
        "fact_type": "decision",
        "subject": "Rivera Labs",
        "body": "Team decided to move Rivera Labs into screening after the intro call.",
        "payload": {"stage": "screening"},
        "document": "doc-alex-intro-call",
        "confidence": 0.85,
        "valid_from": "2026-07-10T16:30:00+00:00",
        "valid_until": None,
    },
]

ACTOR_ALIASES = [
    {"slug": "alias-alex-email", "founder": "founder-a-cold-start-strong", "alias": "alex@riveralabs.dev", "alias_type": "email"},
    {"slug": "alias-alex-handle", "founder": "founder-a-cold-start-strong", "alias": "arivera-dev", "alias_type": "handle"},
    {"slug": "alias-alex-name", "founder": "founder-a-cold-start-strong", "alias": "Alex Rivera", "alias_type": "name"},
]


def get_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(
            "SUPABASE_URL / SUPABASE_SERVICE_KEY not set in .env — nothing to seed.\n"
            "Copy .env.example to .env and fill in Supabase credentials, then re-run:\n"
            "  python db/seed/seed.py"
        )
        sys.exit(0)
    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def upsert(client, table: str, rows: list[dict], on_conflict: str = "id"):
    if not rows:
        return
    client.table(table).upsert(rows, on_conflict=on_conflict).execute()
    print(f"  upserted {len(rows)} row(s) -> {table}")


def main():
    client = get_client()
    print("Seeding VC Brain demo data (docs/14-SEED-DATA-SPEC.md)...")

    print("1. Thesis profiles")
    upsert(client, "thesis_profiles", THESES)

    print("2. Founders")
    founder_rows = [
        {"id": f["id"], "display_name": f["display_name"], "domain_affinity": f["domain_affinity"]}
        for f in FOUNDERS
    ]
    upsert(client, "founders", founder_rows)

    print("3. Founder genome snapshots + score history")
    # Single current snapshot per founder for this seed run — recorded_at is
    # pinned per slug (not `NOW()` on every run) so re-seeding is idempotent.
    genome_rows = []
    for slug, (exec_v, tech, resil, footprint, network) in GENOME_TARGETS.items():
        genome_rows.append({
            "founder_id": sid(slug),
            "execution_velocity": exec_v,
            "technical_depth": tech,
            "resilience_proxy": resil,
            "public_footprint_depth": footprint,
            "network_embeddedness": network,
            "confidence": 0.75,
            "recorded_at": iso(days_ago(0).replace(hour=0, minute=0, second=0, microsecond=0)),
        })
    upsert(client, "founder_genome_snapshots", genome_rows, on_conflict="founder_id,recorded_at")

    score_rows = []
    for slug, scores in FOUNDER_SCORE_HISTORY.items():
        for i, score in enumerate(scores):
            # Truncate to midnight so re-seeding upserts the same row instead
            # of drifting by the few seconds between script runs (same fix
            # as the genome snapshot recorded_at above).
            recorded_at = days_ago((len(scores) - i) * 30).replace(hour=0, minute=0, second=0, microsecond=0)
            score_rows.append({
                "founder_id": sid(slug),
                "score": score,
                "confidence": 0.7,
                "recorded_at": iso(recorded_at),
            })
    upsert(client, "founder_score_history", score_rows, on_conflict="founder_id,recorded_at")

    print("4. Companies")
    company_rows = [
        {"id": sid(c["slug"]), "name": c["name"], "domain": c["domain"], "sector": c["sector"], "status": c["status"]}
        for c in COMPANIES
    ]
    upsert(client, "companies", company_rows)

    print("5. Opportunities")
    active_thesis_id = sid("thesis-ai-infra-eu")
    opp_rows = []
    for o in OPPORTUNITIES:
        opp_rows.append({
            "id": sid(o["slug"]),
            "founder_id": sid(o["founder"]),
            "company_id": sid(o["company"]),
            "thesis_profile_id": active_thesis_id,
            "source": o["source"],
            "discovery_channel": o.get("discovery_channel"),
            "triggering_signal": o.get("triggering_signal"),
            "screen_verdict": o.get("screen_verdict"),
            "thesis_fit_score": o.get("thesis_fit_score"),
            "status": o["status"],
            "has_contradiction": o.get("has_contradiction", False),
        })
    upsert(client, "opportunities", opp_rows)

    print("5b. Decision log for funded portfolio")
    decision_rows = []
    for o in OPPORTUNITIES:
        if o.get("status") != "funded":
            continue
        funded_at = days_ago(int(o.get("funded_days_ago", 30)))
        decision_rows.append({
            "id": sid(f"decision-{o['slug']}"),
            "opportunity_id": sid(o["slug"]),
            "recommendation": "yes",
            "confidence": 0.82,
            "key_unknowns": [],
            "bull_summary": f"Funded {o['slug']} — thesis-aligned $100K check.",
            "bear_summary": "Early-stage execution risk remains.",
            "signal_at": iso(funded_at - timedelta(hours=20)),
            "screening_at": iso(funded_at - timedelta(hours=16)),
            "diligence_at": iso(funded_at - timedelta(hours=6)),
            "decision_at": iso(funded_at),
        })
    if decision_rows:
        upsert(client, "decision_log", decision_rows)

    print("6. Seeded contradiction (claims + evidence + validations)")
    contradiction_opp_id = sid("opp-contradiction")
    for c in CONTRADICTION_CLAIMS:
        claim_id = sid(c["slug"])
        upsert(client, "claims", [{
            "id": claim_id,
            "opportunity_id": contradiction_opp_id,
            "text": c["text"],
            "slide_locator": c["slide_locator"],
            "source": "deck",
        }])
        deck_evidence_id = sid(f"{c['slug']}-deck-evidence")
        contra_evidence_id = sid(f"{c['slug']}-contra-evidence")
        upsert(client, "evidence", [
            {
                "id": deck_evidence_id,
                "source_type": "deck",
                "source_locator": c["slide_locator"],
                "evidence_snippet": c["text"],
                "confidence": 0.95,
            },
            {
                "id": contra_evidence_id,
                **c["contradicting_evidence"],
            },
        ])
        upsert(client, "claim_evidence_links", [
            {"claim_id": claim_id, "evidence_id": deck_evidence_id, "relation": "supports", "confidence": 0.95},
            {"claim_id": claim_id, "evidence_id": contra_evidence_id, "relation": "contradicts",
             "confidence": c["contradicting_evidence"]["confidence"]},
        ], on_conflict="claim_id,evidence_id")
        upsert(client, "claim_validations", [{
            "claim_id": claim_id,
            "status": c["validation_status"],
            "trust_score": c["trust_score"],
            "contradiction_reason": "Deck claim not corroborated by public signals" if c["validation_status"] == "contradicted" else None,
        }], on_conflict="claim_id")
        if c["validation_status"] == "contradicted":
            upsert(client, "contradiction_events", [{
                "claim_id": claim_id,
                "opportunity_id": contradiction_opp_id,
                "description": f"{c['text']!r} contradicted by {c['contradicting_evidence']['source_locator']}",
            }], on_conflict="claim_id")

    # `memos` has no unique constraint on opportunity_id (a real memo can be
    # regenerated), so upsert manually: update if a row exists, else insert.
    memo_sections = [
        {"title": "Executive Summary", "content": "NovaMetrics offers AI-powered revenue forecasting for B2B SaaS.", "not_disclosed": False},
        {"title": "Financials", "content": None, "not_disclosed": True},
    ]
    existing_memo = client.table("memos").select("id").eq("opportunity_id", contradiction_opp_id).limit(1).execute()
    if existing_memo.data:
        client.table("memos").update({"sections": memo_sections}).eq("id", existing_memo.data[0]["id"]).execute()
    else:
        client.table("memos").insert({"opportunity_id": contradiction_opp_id, "sections": memo_sections}).execute()
    print("  upserted 1 row(s) -> memos")

    print("7. Wayback snapshots (DataPulse)")
    datapulse_id = sid("company-datapulse")
    wayback_rows = [
        {**snap, "company_id": datapulse_id, "domain": "datapulse.io", "confidence": 0.7}
        for snap in WAYBACK_SNAPSHOTS
    ]
    upsert(client, "wayback_snapshots", wayback_rows, on_conflict="company_id,snapshot_at")

    print("8. Network graph (nodes, edges, proximity)")
    node_rows = []
    for n in NETWORK_NODES:
        row = {"id": sid(n["slug"]), "type": n["type"], "label": n["label"], "confidence": n["confidence"], "tags": n["tags"]}
        if n["slug"] in FOUNDER_SLUGS:
            row["ref_founder_id"] = sid(n["slug"])
        if n["slug"] in {c["slug"] for c in COMPANIES}:
            row["ref_company_id"] = sid(n["slug"])
        node_rows.append(row)
    upsert(client, "network_nodes", node_rows)

    edge_rows = [
        {
            "from_node_id": sid(e["from"]),
            "to_node_id": sid(e["to"]),
            "relation_type": e["relation_type"],
            "weight": e["weight"],
            "first_seen_at": e["first_seen_at"],
        }
        for e in NETWORK_EDGES
    ]
    upsert(client, "network_edges", edge_rows, on_conflict="from_node_id,to_node_id,relation_type")

    proximity_rows = [
        {
            "founder_id": sid(slug),
            "proximity_score": p["proximity_score"],
            "confidence": p["confidence"],
            "path_count": p["path_count"],
            "disclosure": DISCLOSURE_TEXT,
        }
        for slug, p in NETWORK_PROXIMITY.items()
    ]
    upsert(client, "network_proximity_scores", proximity_rows, on_conflict="founder_id")

    print("9. Memory layer (documents, chunks, facts, aliases)")
    for doc in MEMORY_DOCUMENTS:
        doc_id = sid(doc["slug"])
        upsert(client, "documents", [{
            "id": doc_id,
            "title": doc["title"],
            "doc_type": doc["doc_type"],
            "raw_text": "\n\n".join(doc["chunks"]),
            "founder_id": sid(doc["founder"]),
            "company_id": sid(doc["company"]),
            "source_type": doc["source_type"],
            "source_locator": doc["source_locator"],
            "source_timestamp": doc["source_timestamp"],
        }])
        chunk_rows = [
            {
                "id": sid(f"{doc['slug']}-chunk-{i}"),
                "document_id": doc_id,
                "chunk_index": i,
                "content": content,
                "embedding": fake_embedding(f"{doc['slug']}-chunk-{i}"),
                "founder_id": sid(doc["founder"]),
                "company_id": sid(doc["company"]),
                "source_type": doc["source_type"],
                "source_locator": f"{doc['source_locator']}#chunk-{i}",
                "source_timestamp": doc["source_timestamp"],
            }
            for i, content in enumerate(doc["chunks"])
        ]
        upsert(client, "document_chunks", chunk_rows)

    doc_by_slug = {d["slug"]: d for d in MEMORY_DOCUMENTS}
    fact_rows = []
    for f in MEMORY_FACTS:
        doc = doc_by_slug[f["document"]]
        fact_rows.append({
            "id": sid(f["slug"]),
            "fact_type": f["fact_type"],
            "subject": f["subject"],
            "body": f["body"],
            "payload": f["payload"],
            "founder_id": sid(doc["founder"]),
            "company_id": sid(doc["company"]),
            "document_id": sid(doc["slug"]),
            "confidence": f["confidence"],
            "valid_from": f["valid_from"],
            "valid_until": f["valid_until"],
            "source_type": doc["source_type"],
            "source_locator": doc["source_locator"],
            "source_timestamp": doc["source_timestamp"],
        })
    upsert(client, "memory_facts", fact_rows)

    alias_rows = [
        {
            "id": sid(a["slug"]),
            "founder_id": sid(a["founder"]),
            "alias": a["alias"],
            "alias_type": a["alias_type"],
        }
        for a in ACTOR_ALIASES
    ]
    upsert(client, "actor_aliases", alias_rows)

    print("\nSeed complete. Verify with:")
    print("  GET /api/v1/thesis/active  -> Pre-seed AI Infra EU")
    print("  GET /api/v1/opportunities  -> 6 seeded opportunities")
    print("  GET /api/v1/memory/facts?subject=Rivera  -> current facts (invalidated $500K claim hidden)")


if __name__ == "__main__":
    main()
