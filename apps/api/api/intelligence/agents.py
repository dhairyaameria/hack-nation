"""Agent C — Analyst -> Validator -> Referee pipeline.

Real version: Analyst + Referee use OpenAI structured JSON output;
Validator cross-checks every claim against Tavily web search before an
LLM classifies agreement (`docs/04-INTELLIGENCE-TRUST.md` §2). Every stage
falls back to the Wave 1 deterministic heuristic when the relevant key is
missing or a call fails, so the pipeline shape is always provable and
never crashes or fabricates data (`docs/00-OVERVIEW.md` §4 rule 3).
"""

from __future__ import annotations

import uuid

from api.core import gold_features
from api.intelligence import llm, retrieval

VALID_STATUSES = {"verified", "contradicted", "weakly_supported", "unknown"}
VALID_TRENDS = {"improving", "stable", "declining"}
VALID_AXES = {"founder", "market", "idea_vs_market"}

REQUIRED_MEMO_SECTIONS = [
    "Company snapshot",
    "Investment hypotheses",
    "SWOT",
    "Problem & product",
    "Traction & KPIs",
]


# ---------------------------------------------------------------------------
# Analyst — bull case, 3 independent axes
# ---------------------------------------------------------------------------


def _heuristic_analyst(claims: list[dict]) -> dict:
    n = len(claims)
    richness = min(1.0, 0.3 + 0.15 * n)
    market_label = "bullish" if n >= 4 else "neutral" if n >= 1 else "bear"
    return {
        "axis_scores": [
            {"axis": "founder", "value": round(richness, 2), "trend": "stable", "confidence": 0.4 if n else 0.2, "evidence": []},
            {"axis": "market", "value": market_label, "trend": "stable", "confidence": 0.35, "evidence": []},
            {"axis": "idea_vs_market", "value": round(richness * 0.9, 2), "trend": "stable", "confidence": 0.35, "evidence": []},
        ],
        "prompt_version": "heuristic-analyst-v1",
    }


def _normalize_axis_scores(raw: list[dict]) -> list[dict] | None:
    out = []
    seen = set()
    for row in raw:
        axis = row.get("axis")
        if axis not in VALID_AXES or axis in seen:
            continue
        seen.add(axis)
        value = row.get("value")
        if axis == "market":
            if value not in {"bullish", "neutral", "bear"}:
                value = "neutral"
        else:
            try:
                value = round(max(0.0, min(1.0, float(value))), 2)
            except (TypeError, ValueError):
                value = 0.5
        trend = row.get("trend") if row.get("trend") in VALID_TRENDS else "stable"
        try:
            confidence = round(max(0.0, min(1.0, float(row.get("confidence", 0.3)))), 2)
        except (TypeError, ValueError):
            confidence = 0.3
        out.append({"axis": axis, "value": value, "trend": trend, "confidence": confidence, "evidence": []})
    return out if len(out) == 3 else None


def run_analyst(company_name: str, claims: list[dict], founder_axis_override: dict | None = None) -> dict:
    """`founder_axis_override` (from `api.core.gold_features`) replaces the
    claims-derived Founder axis with one computed from real Gold features +
    the persistent Founder Score whenever the founder has connector/Genome
    data — claims are a weak proxy for founder quality; Gold features are
    the real thing (`docs/04-INTELLIGENCE-TRUST.md` §2 item 1)."""
    if llm.is_available():
        claim_text = "\n".join(f"- {c.get('text', '')}" for c in claims) or "(no claims extracted from deck)"
        system = (
            "You are a bull-case venture capital analyst. Score three INDEPENDENT axes for an "
            "early-stage startup based ONLY on the claims given. Never combine them into one "
            "overall score. Be optimistic but grounded in the evidence given — do not invent facts "
            "not present in the claims.\n\n"
            "Return strict JSON of the shape:\n"
            '{"axis_scores": [\n'
            '  {"axis": "founder", "value": <0.0-1.0>, "trend": "improving|stable|declining", "confidence": <0.0-1.0>},\n'
            '  {"axis": "market", "value": "bullish|neutral|bear", "trend": "improving|stable|declining", "confidence": <0.0-1.0>},\n'
            '  {"axis": "idea_vs_market", "value": <0.0-1.0>, "trend": "improving|stable|declining", "confidence": <0.0-1.0>}\n'
            "]}\n"
            "confidence should reflect how much evidence backs the score — few/vague claims means low confidence."
        )
        user = f"Company: {company_name}\nClaims from pitch deck:\n{claim_text}"
        data = llm.chat_json(system, user)
        normalized = _normalize_axis_scores(data.get("axis_scores", [])) if data else None
        if normalized:
            result = {"axis_scores": normalized, "prompt_version": f"openai:{llm.MODEL}:analyst-v1"}
            return _apply_founder_override(result, founder_axis_override)
    return _apply_founder_override(_heuristic_analyst(claims), founder_axis_override)


def _apply_founder_override(result: dict, founder_axis_override: dict | None) -> dict:
    if founder_axis_override is None:
        return result
    result["axis_scores"] = [founder_axis_override if a["axis"] == "founder" else a for a in result["axis_scores"]]
    result["prompt_version"] += "+gold_features_v1"
    return result


# ---------------------------------------------------------------------------
# Validator — bear case, cross-checks every claim
# ---------------------------------------------------------------------------


def _unknown_validation(claim_id: str, reason: str) -> dict:
    return {
        "claim_id": claim_id,
        "status": "unknown",
        "trust_score": 0.5,
        "contradiction_reason": None,
        "required_followup": reason,
        "web_evidence": [],
        "prompt_version": "no-corroboration-source",
    }


def _classify_claim_with_evidence(claim_text: str, company_name: str, evidence: list[dict]) -> dict | None:
    evidence_text = "\n".join(f"- [{e['url']}] {e['content']}" for e in evidence)
    system = (
        "You are a bear-case venture capital validator. Cross-check a startup's claim against "
        "independent web search results. Be skeptical — flag any conflict, even partial, as "
        "'contradicted' or 'weakly_supported'. Only use 'verified' if the search results directly "
        "confirm the specific claim. If the search results are unrelated or insufficient to judge, "
        "say 'unknown'. NEVER invent evidence not present in the search results.\n\n"
        "trust_score calibration (anchor to these, do not default to 0 for lack of evidence):\n"
        "- status='unknown' -> trust_score MUST be ~0.5 (absence of evidence is not evidence of falsehood).\n"
        "- status='verified' -> trust_score 0.7-1.0, scaled by how directly the results confirm the claim.\n"
        "- status='weakly_supported' -> trust_score 0.5-0.7.\n"
        "- status='contradicted' -> trust_score 0.0-0.3, scaled by how directly the results conflict.\n\n"
        "Return strict JSON:\n"
        '{"status": "verified|contradicted|weakly_supported|unknown", "trust_score": <0.0-1.0>, '
        '"contradiction_reason": <string or null>, "required_followup": <string or null>}'
    )
    user = f"Company: {company_name}\nClaim: {claim_text!r}\n\nWeb search results:\n{evidence_text}"
    data = llm.chat_json(system, user)
    if not data or data.get("status") not in VALID_STATUSES:
        return None
    status = data["status"]
    if status == "unknown":
        # Absence of evidence is not evidence of falsehood — never let a
        # miscalibrated LLM score an "unknown" claim as if it were disproven.
        trust_score = 0.5
    else:
        try:
            trust_score = round(max(0.0, min(1.0, float(data.get("trust_score", 0.5)))), 2)
        except (TypeError, ValueError):
            trust_score = 0.5
    return {
        "status": status,
        "trust_score": trust_score,
        "contradiction_reason": data.get("contradiction_reason"),
        "required_followup": data.get("required_followup"),
    }


def _validate_claim(claim: dict, company_name: str) -> dict:
    claim_id = claim.get("claim_id")
    text = claim.get("text", "")

    if not retrieval.is_available():
        return _unknown_validation(claim_id, "No external corroboration source configured (add TAVILY_API_KEY).")

    evidence = retrieval.search(f"{company_name} {text}")
    if not evidence:
        return {**_unknown_validation(claim_id, "Tavily returned no related results — needs manual diligence."), "prompt_version": "tavily:no-results"}

    if llm.is_available():
        classified = _classify_claim_with_evidence(text, company_name, evidence)
        if classified:
            return {**classified, "claim_id": claim_id, "web_evidence": evidence, "prompt_version": f"tavily+openai:{llm.MODEL}:validator-v1"}

    # Found web results but no LLM to interpret them — surface as weakly
    # supported (found *something* related) rather than fabricating a verdict.
    return {
        "claim_id": claim_id,
        "status": "weakly_supported",
        "trust_score": 0.5,
        "contradiction_reason": None,
        "required_followup": "Found related web results but no LLM configured to classify agreement — manual review needed.",
        "web_evidence": evidence,
        "prompt_version": "tavily:unclassified",
    }


def run_validator(claims: list[dict], company_name: str) -> list[dict]:
    return [_validate_claim(c, company_name) for c in claims]


# ---------------------------------------------------------------------------
# Referee — resolves Analyst/Validator disagreement into the final memo
# ---------------------------------------------------------------------------


def _heuristic_referee(
    company_name: str,
    claims: list[dict],
    analyst_out: dict,
    research_blob: str = "",
) -> dict:
    has_traction_claim = any(
        "traction" in c.get("text", "").lower() or "$" in c.get("text", "") or "raised" in c.get("text", "").lower()
        for c in claims
    )
    snapshot_bits = [f"{company_name} — {len(claims)} research/deck claim(s)."]
    if research_blob:
        snapshot_bits.append(research_blob[:400].replace("\n", " "))
    claim_texts = [c.get("text", "") for c in claims if c.get("text")]
    sections = [
        {"title": "Company snapshot", "content": " ".join(snapshot_bits)[:600], "not_disclosed": False},
        {
            "title": "Investment hypotheses",
            "content": (claim_texts[0] if claim_texts else None) and f"Hypothesis from public signals: {claim_texts[0]}",
            "not_disclosed": not claim_texts,
        },
        {
            "title": "SWOT",
            "content": ("Strengths/opportunities inferred from public claims:\n- " + "\n- ".join(claim_texts[:3])) if claim_texts else None,
            "not_disclosed": not claim_texts,
        },
        {"title": "Problem & product", "content": claim_texts[0] if claim_texts else None, "not_disclosed": not claim_texts},
        {
            "title": "Traction & KPIs",
            "content": next(
                (c for c in claim_texts if any(k in c.lower() for k in ("$", "raised", "arr", "customers", "users", "funding"))),
                None,
            ) if has_traction_claim else None,
            "not_disclosed": not has_traction_claim,
        },
    ]
    return {"sections": sections, "axis_scores": analyst_out["axis_scores"], "prompt_version": "heuristic-referee-v2"}


def _llm_referee(
    company_name: str,
    claims: list[dict],
    analyst_out: dict,
    validations: list[dict],
    *,
    research_blob: str = "",
    founder_name: str = "",
) -> dict | None:
    val_by_id = {v["claim_id"]: v for v in validations}
    claims_block = "\n".join(
        f"- {c.get('text', '')} [validator status: {val_by_id.get(c.get('claim_id'), {}).get('status', 'unknown')}"
        f"{', reason: ' + val_by_id[c['claim_id']]['contradiction_reason'] if val_by_id.get(c.get('claim_id'), {}).get('contradiction_reason') else ''}]"
        for c in claims
    ) or "(no structured claims yet)"
    axis_block = "\n".join(f"- {a['axis']}: {a['value']} (confidence {a['confidence']})" for a in analyst_out["axis_scores"])
    research_block = (research_blob or "").strip()[:7000] or "(no live research dossier)"

    system = (
        "You are the Referee in a VC diligence pipeline. You receive (1) a LIVE RESEARCH DOSSIER "
        "from GitHub/LinkedIn/HN/arXiv/Perplexity/Tavily and (2) structured claims with validator "
        "verdicts. Write a concise investment memo grounded in that dossier.\n"
        "HARD RULES:\n"
        "1. USE the research dossier to fill Company snapshot, Problem & product, Investment "
        "hypotheses, and SWOT whenever evidence exists — do NOT leave those 'not disclosed' if "
        "the dossier describes the company/founder.\n"
        "2. Traction & KPIs: only state numbers that appear in claims/dossier; otherwise "
        "not_disclosed=true (never invent ARR/customers/funding).\n"
        "3. Validator 'contradicted' claims must be flagged, not presented as fact.\n"
        "4. Be brief — no padding.\n\n"
        "Return strict JSON:\n"
        '{"sections": [\n'
        '  {"title": "Company snapshot", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "Investment hypotheses", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "SWOT", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "Problem & product", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "Traction & KPIs", "content": <string or null>, "not_disclosed": <bool>}\n'
        "]}"
    )
    user = (
        f"Company: {company_name}\nFounder: {founder_name or 'unknown'}\n\n"
        f"LIVE RESEARCH DOSSIER:\n{research_block}\n\n"
        f"Claims + validator verdicts:\n{claims_block}\n\n"
        f"Analyst axis scores:\n{axis_block}"
    )
    data = llm.chat_json(system, user)
    if not data or "sections" not in data:
        return None

    by_title = {s.get("title"): s for s in data["sections"] if isinstance(s, dict)}
    sections = []
    for title in REQUIRED_MEMO_SECTIONS:
        s = by_title.get(title)
        if not s:
            sections.append({"title": title, "content": None, "not_disclosed": True})
            continue
        content = s.get("content")
        if isinstance(content, str) and content.strip().lower() in {"not_disclosed", "not_disclosed=true", "null", "none", "n/a"}:
            content = None
        undisclosed = bool(s.get("not_disclosed")) or content is None or content == ""
        sections.append({
            "title": title,
            "content": None if undisclosed else content,
            "not_disclosed": undisclosed,
        })
    return {"sections": sections, "axis_scores": analyst_out["axis_scores"], "prompt_version": f"openai:{llm.MODEL}:referee-v2"}


def run_referee(
    company_name: str,
    claims: list[dict],
    analyst_out: dict,
    validations: list[dict],
    *,
    research_blob: str = "",
    founder_name: str = "",
) -> dict:
    if llm.is_available():
        result = _llm_referee(
            company_name,
            claims,
            analyst_out,
            validations,
            research_blob=research_blob,
            founder_name=founder_name,
        )
        if result:
            return result
    return _heuristic_referee(company_name, claims, analyst_out, research_blob=research_blob)


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------


def _build_founder_axis_override(founder_id: str | None) -> dict | None:
    """Gold features -> Founder axis, per `docs/04-INTELLIGENCE-TRUST.md`
    §2 item 1. Also appends the freshly-computed Founder Score to the
    founder's persistent history (`docs/02-DATA-FOUNDATION.md` §4) — a
    real score update, not just a display value. Returns `None` for a
    true cold-start founder (no Genome, no Bronze signals), so the caller
    falls back to the claims-only heuristic instead.
    """
    if not founder_id:
        return None
    gold = gold_features.get_gold_features(founder_id)
    if gold is None:
        return None
    score = gold_features.compute_founder_score(gold)
    gold_features.append_score_history(founder_id, score, gold.get("confidence", 0.5))
    trend = gold_features.get_score_trend(founder_id)
    return gold_features.founder_axis_from_gold(gold, score, trend)


def run_pipeline(
    opportunity_id: str,
    company_name: str,
    claims: list[dict],
    founder_id: str | None = None,
    *,
    founder_name: str = "",
    research_blob: str = "",
) -> dict:
    trace_id = f"trace-{uuid.uuid4().hex[:8]}"
    # Ensure every claim has an id before validate/persist.
    for c in claims:
        if not c.get("claim_id"):
            c["claim_id"] = f"claim-{uuid.uuid4().hex[:10]}"
    claim_ids = [c.get("claim_id") for c in claims]

    founder_axis_override = _build_founder_axis_override(founder_id)
    analyst_out = run_analyst(company_name, claims, founder_axis_override)
    validations = run_validator(claims, company_name)
    referee_out = run_referee(
        company_name,
        claims,
        analyst_out,
        validations,
        research_blob=research_blob,
        founder_name=founder_name,
    )

    trace = {
        "trace_id": trace_id,
        "opportunity_id": opportunity_id,
        "stages": [
            {
                "stage": "research",
                "inputs_used": [company_name, founder_name] if founder_name else [company_name],
                "decision_rule_or_prompt_version": "live-connectors-v1",
                "output_claim_ids": claim_ids,
            },
            {"stage": "analyst", "inputs_used": claim_ids, "decision_rule_or_prompt_version": analyst_out["prompt_version"], "output_claim_ids": claim_ids},
            {"stage": "validate", "inputs_used": claim_ids, "decision_rule_or_prompt_version": ",".join({v["prompt_version"] for v in validations}) or "n/a", "output_claim_ids": claim_ids},
            {"stage": "referee", "inputs_used": claim_ids, "decision_rule_or_prompt_version": referee_out["prompt_version"], "output_claim_ids": claim_ids},
        ],
    }

    val_by_id = {v["claim_id"]: v for v in validations}
    claims_with_trust = []
    for c in claims:
        v = val_by_id.get(c.get("claim_id"), {})
        locator = c.get("slide_locator") or "unknown"
        source_type = "outbound_research" if locator == "outbound_research" else "deck"
        evidence = [{
            "source_type": source_type,
            "source_locator": locator,
            "evidence_snippet": c.get("text", ""),
            "confidence": 0.75 if source_type == "outbound_research" else 0.9,
        }]
        for web in v.get("web_evidence", []):
            evidence.append({
                "source_type": "web",
                "source_locator": web.get("url", "unknown"),
                "evidence_snippet": web.get("content", ""),
                "confidence": 0.6,
            })
        claims_with_trust.append({
            "claim_id": c.get("claim_id"),
            "text": c.get("text"),
            "trust_score": v.get("trust_score", 0.5),
            "validation_status": v.get("status", "unknown"),
            "contradiction_reason": v.get("contradiction_reason"),
            "evidence": evidence,
        })

    return {
        "axis_scores": referee_out["axis_scores"],
        "memo": {"sections": referee_out["sections"]},
        "claims": claims_with_trust,
        "trace": trace,
        "research_channels": [],
    }
