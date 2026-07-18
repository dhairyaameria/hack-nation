"""Agent C — Analyst -> Validator -> Referee pipeline.

Wave 1: deterministic heuristic stubs (no OpenAI/Tavily calls — no keys
required to demo the pipeline shape). Every function signature here is
the one Wave 2 keeps; only the body swaps to real LLM/Tavily calls per
`docs/04-INTELLIGENCE-TRUST.md` §2. Every stage still writes a real
reasoning trace so `docs/00-OVERVIEW.md` §4 rule 4 (evidence locator on
every factual output) holds even before real agents are wired in.
"""

from __future__ import annotations

import uuid

PROMPT_VERSION = "wave1-heuristic-v1"

REQUIRED_MEMO_SECTIONS = [
    "Company snapshot",
    "Investment hypotheses",
    "SWOT",
    "Problem & product",
    "Traction & KPIs",
]


def run_analyst(company_name: str, claims: list[dict]) -> dict:
    """Draft axis scores from claim richness. Bull-case framing.

    Real version (Wave 2): OpenAI structured output over Gold features +
    claims. This stub scores purely on claim count/keyword density so the
    3-axis *shape* (independent, trended, confidence-qualified) is provable
    end-to-end without an LLM key.
    """
    n = len(claims)
    richness = min(1.0, 0.3 + 0.15 * n)
    market_label = "bullish" if n >= 4 else "neutral" if n >= 1 else "bear"

    axis_scores = [
        {"axis": "founder", "value": round(richness, 2), "trend": "stable", "confidence": 0.4 if n else 0.2, "evidence": []},
        {"axis": "market", "value": market_label, "trend": "stable", "confidence": 0.35, "evidence": []},
        {"axis": "idea_vs_market", "value": round(richness * 0.9, 2), "trend": "stable", "confidence": 0.35, "evidence": []},
    ]
    return {"axis_scores": axis_scores}


def run_validator(claims: list[dict]) -> list[dict]:
    """Cross-checks every claim. Bear-case framing.

    Real version (Wave 2): Tavily/Perplexity retrieval per claim
    (`docs/04-INTELLIGENCE-TRUST.md` §2 item 2). Without those keys, a
    freshly-submitted claim has no corroboration available — per the
    binding rule "absence of evidence = unknown, never bad"
    (`docs/00-OVERVIEW.md` §4 rule 3/6), every claim here is `unknown`,
    not fabricated as verified or penalized as contradicted.
    """
    validations = []
    for claim in claims:
        validations.append({
            "claim_id": claim.get("claim_id"),
            "status": "unknown",
            "trust_score": 0.5,
            "contradiction_reason": None,
            "required_followup": "No external corroboration source configured yet (Tavily/Perplexity key required for Wave 2 validation).",
        })
    return validations


def run_referee(company_name: str, claims: list[dict], analyst_out: dict, validations: list[dict]) -> dict:
    """Resolves Analyst/Validator disagreement into a final memo + axis
    scores. Missing data is flagged `not_disclosed`, never fabricated
    (`docs/00-OVERVIEW.md` §4 rule 3).
    """
    has_traction_claim = any("traction" in c.get("text", "").lower() or "$" in c.get("text", "") for c in claims)
    sections = [
        {"title": "Company snapshot", "content": f"{company_name} — inbound submission, {len(claims)} claims extracted.", "not_disclosed": False},
        {"title": "Investment hypotheses", "content": "Draft hypotheses pending deeper research (Wave 2 Perplexity sweep).", "not_disclosed": False},
        {"title": "SWOT", "content": None, "not_disclosed": True},
        {"title": "Problem & product", "content": claims[0]["text"] if claims else None, "not_disclosed": len(claims) == 0},
        {"title": "Traction & KPIs", "content": next((c["text"] for c in claims if "traction" in c.get("text", "").lower() or "$" in c.get("text", "")), None) if has_traction_claim else None, "not_disclosed": not has_traction_claim},
    ]
    return {"sections": sections, "axis_scores": analyst_out["axis_scores"]}


def run_pipeline(opportunity_id: str, company_name: str, claims: list[dict]) -> dict:
    """Runs Analyst -> Validator -> Referee and returns axis scores, memo,
    and a reasoning trace for the drill-down view.
    """
    trace_id = f"trace-{uuid.uuid4().hex[:8]}"
    claim_ids = [c.get("claim_id") for c in claims]

    analyst_out = run_analyst(company_name, claims)
    validations = run_validator(claims)
    referee_out = run_referee(company_name, claims, analyst_out, validations)

    trace = {
        "trace_id": trace_id,
        "opportunity_id": opportunity_id,
        "stages": [
            {"stage": "analyst", "inputs_used": claim_ids, "decision_rule_or_prompt_version": PROMPT_VERSION, "output_claim_ids": claim_ids},
            {"stage": "validate", "inputs_used": claim_ids, "decision_rule_or_prompt_version": PROMPT_VERSION, "output_claim_ids": claim_ids},
            {"stage": "referee", "inputs_used": claim_ids, "decision_rule_or_prompt_version": PROMPT_VERSION, "output_claim_ids": claim_ids},
        ],
    }

    claims_with_trust = [
        {
            "claim_id": c.get("claim_id"),
            "text": c.get("text"),
            "trust_score": v["trust_score"],
            "validation_status": v["status"],
            "evidence": [{
                "source_type": "deck",
                "source_locator": c.get("slide_locator", "unknown"),
                "evidence_snippet": c.get("text", ""),
                "confidence": 0.9,
            }],
        }
        for c, v in zip(claims, validations)
    ]

    return {
        "axis_scores": referee_out["axis_scores"],
        "memo": {"sections": referee_out["sections"]},
        "claims": claims_with_trust,
        "trace": trace,
    }
