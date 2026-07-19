"""Perplexity-backed inbound opportunity rerank.

UI-free core used by:
  1. `POST /api/v1/inbound/rerank`  (manual button later)
  2. `python -m jobs.pipelines.inbound_rerank_cron`  (cron / scheduler)

Reads inbound opportunities + pitch-deck text from the DB/Storage, scores
them against the active thesis via Perplexity, and writes
`inbound_rank` / `thesis_fit_score` / rationale back to `opportunities`.

Scale note: see `docs/19-INBOUND-RERANK.md` — current design loads the full
inbound set into one Perplexity call (fine for a small demo DB; not for
production volume).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from api.agent import thesis_store
from api.core import opportunity_store
from api.ingestion import deck_parser, deck_storage
from api.intelligence import perplexity

Trigger = Literal["manual", "cron", "api"]

SYSTEM_PROMPT = (
    "You are a venture analyst for an early-stage fund. Rank inbound pitch "
    "applications against the fund thesis. Use web context when helpful, but "
    "do NOT invent company-specific metrics that are not in the deck text or "
    "clearly supported by public sources. Prefer explicit 'unknown' over "
    "fabrication. Return ONLY a JSON object matching the schema in the user "
    "message — no prose outside JSON."
)


def rerank_inbound(*, trigger: Trigger = "api") -> dict[str, Any]:
    """Rerank every inbound opportunity. Safe to call from HTTP or cron."""
    run_id = str(uuid.uuid4())
    ranked_at = datetime.now(timezone.utc).isoformat()

    thesis = thesis_store.get_active_thesis()
    if thesis is None:
        return {
            "ok": False,
            "error": "No active thesis — activate one before reranking.",
            "run_id": run_id,
            "trigger": trigger,
        }

    inbound = opportunity_store.list_inbound_for_rerank()
    if not inbound:
        return {
            "ok": True,
            "run_id": run_id,
            "trigger": trigger,
            "thesis_id": thesis["id"],
            "count": 0,
            "rankings": [],
            "note": "No inbound opportunities to rank.",
        }

    candidates = [_build_candidate(row) for row in inbound]

    if not perplexity.is_available():
        rankings = _heuristic_rank(candidates, thesis)
        opportunity_store.apply_inbound_rankings(
            rankings, run_id=run_id, ranked_at=ranked_at
        )
        return {
            "ok": True,
            "run_id": run_id,
            "trigger": trigger,
            "thesis_id": thesis["id"],
            "provider": "heuristic",
            "count": len(rankings),
            "rankings": rankings,
            "note": "PERPLEXITY_API_KEY missing — used deterministic heuristic fallback.",
        }

    parsed = perplexity.chat_json(
        SYSTEM_PROMPT,
        _user_prompt(thesis, candidates),
    )
    if parsed is None or not isinstance(parsed.get("rankings"), list):
        rankings = _heuristic_rank(candidates, thesis)
        opportunity_store.apply_inbound_rankings(
            rankings, run_id=run_id, ranked_at=ranked_at
        )
        return {
            "ok": True,
            "run_id": run_id,
            "trigger": trigger,
            "thesis_id": thesis["id"],
            "provider": "heuristic",
            "count": len(rankings),
            "rankings": rankings,
            "note": "Perplexity unavailable or returned unusable JSON — heuristic fallback.",
        }

    rankings = _normalize_rankings(parsed["rankings"], candidates, parsed.get("_citations") or [])
    opportunity_store.apply_inbound_rankings(
        rankings, run_id=run_id, ranked_at=ranked_at
    )
    return {
        "ok": True,
        "run_id": run_id,
        "trigger": trigger,
        "thesis_id": thesis["id"],
        "provider": "perplexity",
        "model": perplexity.MODEL,
        "count": len(rankings),
        "rankings": rankings,
        "citations": parsed.get("_citations") or [],
    }


def _build_candidate(row: dict[str, Any]) -> dict[str, Any]:
    deck_text = ""
    storage_path = row.get("deck_storage_path") or ""
    if storage_path:
        raw = deck_storage.download_deck(storage_path)
        if raw:
            deck_text = deck_parser.extract_deck_text(raw)

    if not deck_text:
        claims = row.get("claims") or []
        claim_lines = [c.get("text", "") for c in claims if c.get("text")]
        if claim_lines:
            deck_text = "Claims extracted from deck:\n" + "\n".join(f"- {t}" for t in claim_lines)
        else:
            deck_text = "(no deck text available)"

    return {
        "opportunity_id": row["id"],
        "company_name": row.get("company_name", "Unknown"),
        "founder_name": row.get("founder_name", "Unknown"),
        "screen_verdict": row.get("screen_verdict"),
        "status": row.get("status"),
        "deck_url": row.get("deck_url") or "",
        "deck_excerpt": deck_text[:8000],
    }


def _user_prompt(thesis: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    thesis_block = (
        f"Name: {thesis.get('name')}\n"
        f"Sectors: {', '.join(thesis.get('sectors') or [])}\n"
        f"Stage: {thesis.get('stage')}\n"
        f"Geography: {thesis.get('geography')}\n"
        f"Check size USD: {thesis.get('check_size_usd')}\n"
        f"Risk appetite: {thesis.get('risk_appetite')}\n"
        f"Exclude sectors: {', '.join(thesis.get('exclude_sectors') or []) or 'none'}\n"
        f"Require signals: {', '.join(thesis.get('require_signals') or []) or 'none'}\n"
    )

    opp_blocks = []
    for c in candidates:
        opp_blocks.append(
            f"### {c['opportunity_id']}\n"
            f"Company: {c['company_name']}\n"
            f"Founder: {c['founder_name']}\n"
            f"Screen verdict: {c.get('screen_verdict')}\n"
            f"Deck URL: {c.get('deck_url') or 'n/a'}\n"
            f"Deck / claims text:\n{c['deck_excerpt']}\n"
        )

    schema = (
        "{\n"
        '  "rankings": [\n'
        "    {\n"
        '      "opportunity_id": "<uuid>",\n'
        '      "rank": 1,\n'
        '      "score": 0.0,\n'
        '      "rationale": "<one or two sentences, cite thesis fit>",\n'
        '      "evidence_urls": ["https://..."]\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules: include EVERY opportunity_id exactly once; rank is 1-based "
        "(1 = best fit); score is 0-1 thesis fit; never invent ARR/revenue."
    )

    return (
        f"## Active fund thesis\n{thesis_block}\n"
        f"## Inbound applications ({len(candidates)})\n"
        + "\n".join(opp_blocks)
        + f"\n## Output schema\n{schema}"
    )


def _normalize_rankings(
    raw: list[Any],
    candidates: list[dict[str, Any]],
    global_citations: list[str],
) -> list[dict[str, Any]]:
    by_id = {c["opportunity_id"]: c for c in candidates}
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    for row in raw:
        if not isinstance(row, dict):
            continue
        oid = row.get("opportunity_id")
        if oid not in by_id or oid in seen:
            continue
        seen.add(oid)
        try:
            score = max(0.0, min(1.0, float(row.get("score", 0.5))))
        except (TypeError, ValueError):
            score = 0.5
        evidence = row.get("evidence_urls") or []
        if not isinstance(evidence, list):
            evidence = []
        if not evidence and global_citations:
            evidence = list(global_citations[:3])
        out.append({
            "opportunity_id": oid,
            "company_name": by_id[oid]["company_name"],
            "rank": len(out) + 1,  # re-number after filtering; sorted below
            "score": round(score, 3),
            "rationale": str(row.get("rationale") or "No rationale provided.")[:2000],
            "evidence_urls": [str(u) for u in evidence if u][:5],
        })

    # Append any candidates Perplexity omitted (unknown ≠ drop).
    for c in candidates:
        if c["opportunity_id"] not in seen:
            out.append({
                "opportunity_id": c["opportunity_id"],
                "company_name": c["company_name"],
                "rank": 0,
                "score": 0.3,
                "rationale": "Not scored by model — held at end with low confidence.",
                "evidence_urls": [],
            })

    out.sort(key=lambda r: (-r["score"], r["company_name"]))
    for i, row in enumerate(out, start=1):
        row["rank"] = i
    return out


def _heuristic_rank(
    candidates: list[dict[str, Any]],
    thesis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Deterministic fallback when Perplexity is offline — still writes ranks."""
    sectors = {s.lower() for s in (thesis.get("sectors") or [])}
    scored: list[dict[str, Any]] = []
    for c in candidates:
        text = (c.get("deck_excerpt") or "").lower()
        hits = sum(1 for s in sectors if s.replace("_", " ") in text or s in text)
        richness = min(1.0, len(c.get("deck_excerpt") or "") / 4000)
        score = round(min(1.0, 0.35 + 0.15 * hits + 0.4 * richness), 3)
        if c.get("screen_verdict") == "reject":
            score = round(score * 0.5, 3)
        scored.append({
            "opportunity_id": c["opportunity_id"],
            "company_name": c["company_name"],
            "rank": 0,
            "score": score,
            "rationale": (
                f"Heuristic thesis overlap ({hits} sector hit(s)) — "
                "enable PERPLEXITY_API_KEY for search-grounded ranking."
            ),
            "evidence_urls": [],
        })
    scored.sort(key=lambda r: (-r["score"], r["company_name"]))
    for i, row in enumerate(scored, start=1):
        row["rank"] = i
    return scored
