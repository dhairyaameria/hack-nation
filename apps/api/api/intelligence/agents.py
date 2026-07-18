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


def run_analyst(company_name: str, claims: list[dict]) -> dict:
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
            return {"axis_scores": normalized, "prompt_version": f"openai:{llm.MODEL}:analyst-v1"}
    return _heuristic_analyst(claims)


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


def _heuristic_referee(company_name: str, claims: list[dict], analyst_out: dict) -> dict:
    has_traction_claim = any("traction" in c.get("text", "").lower() or "$" in c.get("text", "") for c in claims)
    sections = [
        {"title": "Company snapshot", "content": f"{company_name} — inbound submission, {len(claims)} claims extracted.", "not_disclosed": False},
        {"title": "Investment hypotheses", "content": "Draft hypotheses pending deeper research.", "not_disclosed": False},
        {"title": "SWOT", "content": None, "not_disclosed": True},
        {"title": "Problem & product", "content": claims[0]["text"] if claims else None, "not_disclosed": len(claims) == 0},
        {"title": "Traction & KPIs", "content": next((c["text"] for c in claims if "traction" in c.get("text", "").lower() or "$" in c.get("text", "")), None) if has_traction_claim else None, "not_disclosed": not has_traction_claim},
    ]
    return {"sections": sections, "axis_scores": analyst_out["axis_scores"], "prompt_version": "heuristic-referee-v1"}


def _llm_referee(company_name: str, claims: list[dict], analyst_out: dict, validations: list[dict]) -> dict | None:
    val_by_id = {v["claim_id"]: v for v in validations}
    claims_block = "\n".join(
        f"- {c.get('text', '')} [validator status: {val_by_id.get(c.get('claim_id'), {}).get('status', 'unknown')}"
        f"{', reason: ' + val_by_id[c['claim_id']]['contradiction_reason'] if val_by_id.get(c.get('claim_id'), {}).get('contradiction_reason') else ''}]"
        for c in claims
    ) or "(no claims extracted from deck)"
    axis_block = "\n".join(f"- {a['axis']}: {a['value']} (confidence {a['confidence']})" for a in analyst_out["axis_scores"])

    system = (
        "You are the Referee in a VC diligence pipeline, resolving disagreement between a bull-case "
        "Analyst and a bear-case Validator. Write a concise investment memo. HARD RULES:\n"
        "1. Any claim the validator marked 'contradicted' must NOT be presented as fact — flag it "
        "explicitly instead (e.g. 'Deck claims X, but this was contradicted by independent evidence').\n"
        "2. If there is no information for a required section, set not_disclosed=true and content=null. "
        "NEVER invent data to fill a gap — a gap-marked memo is more trustworthy than a padded one.\n"
        "3. Be brief — no padding.\n\n"
        "Return strict JSON:\n"
        '{"sections": [\n'
        '  {"title": "Company snapshot", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "Investment hypotheses", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "SWOT", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "Problem & product", "content": <string or null>, "not_disclosed": <bool>},\n'
        '  {"title": "Traction & KPIs", "content": <string or null>, "not_disclosed": <bool>}\n'
        "]}"
    )
    user = f"Company: {company_name}\n\nClaims + validator verdicts:\n{claims_block}\n\nAnalyst axis scores:\n{axis_block}"
    data = llm.chat_json(system, user)
    if not data or "sections" not in data:
        return None

    by_title = {s.get("title"): s for s in data["sections"] if isinstance(s, dict)}
    sections = []
    for title in REQUIRED_MEMO_SECTIONS:
        s = by_title.get(title)
        if not s:
            sections.append({"title": title, "content": None, "not_disclosed": True})
        else:
            sections.append({
                "title": title,
                "content": s.get("content"),
                "not_disclosed": bool(s.get("not_disclosed", s.get("content") is None)),
            })
    return {"sections": sections, "axis_scores": analyst_out["axis_scores"], "prompt_version": f"openai:{llm.MODEL}:referee-v1"}


def run_referee(company_name: str, claims: list[dict], analyst_out: dict, validations: list[dict]) -> dict:
    if llm.is_available():
        result = _llm_referee(company_name, claims, analyst_out, validations)
        if result:
            return result
    return _heuristic_referee(company_name, claims, analyst_out)


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------


def run_pipeline(opportunity_id: str, company_name: str, claims: list[dict]) -> dict:
    trace_id = f"trace-{uuid.uuid4().hex[:8]}"
    claim_ids = [c.get("claim_id") for c in claims]

    analyst_out = run_analyst(company_name, claims)
    validations = run_validator(claims, company_name)
    referee_out = run_referee(company_name, claims, analyst_out, validations)

    trace = {
        "trace_id": trace_id,
        "opportunity_id": opportunity_id,
        "stages": [
            {"stage": "analyst", "inputs_used": claim_ids, "decision_rule_or_prompt_version": analyst_out["prompt_version"], "output_claim_ids": claim_ids},
            {"stage": "validate", "inputs_used": claim_ids, "decision_rule_or_prompt_version": ",".join({v["prompt_version"] for v in validations}) or "n/a", "output_claim_ids": claim_ids},
            {"stage": "referee", "inputs_used": claim_ids, "decision_rule_or_prompt_version": referee_out["prompt_version"], "output_claim_ids": claim_ids},
        ],
    }

    val_by_id = {v["claim_id"]: v for v in validations}
    claims_with_trust = []
    for c in claims:
        v = val_by_id.get(c.get("claim_id"), {})
        evidence = [{
            "source_type": "deck",
            "source_locator": c.get("slide_locator", "unknown"),
            "evidence_snippet": c.get("text", ""),
            "confidence": 0.9,
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
    }
