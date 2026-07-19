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

# Challenge brief memo spec (required + optional). Always emit every title;
# never fabricate. Gap semantics differ by section type (see FOUNDER_SENSITIVE).
REQUIRED_MEMO_SECTIONS = [
    "Company snapshot",
    "Investment hypotheses",
    "SWOT",
    "Problem & product",
    "Traction & KPIs",
]

OPTIONAL_MEMO_SECTIONS = [
    "Team & history",
    "Technology & defensibility",
    "Market sizing",
    "Competition",
    "Financials & round structure",
    "Cap table",
    "Due diligence log",
    "Exit perspective",
]

# Confidential founder-pack items — empty means not_disclosed (withheld).
# Everything else is analyst synthesis: empty means insufficient evidence,
# not "the founder withheld a SWOT / exit strategy."
FOUNDER_SENSITIVE_SECTIONS = {
    "Financials & round structure",
    "Cap table",
}

# Canonical order matches the challenge brief § Investment Memo appendix.
ALL_MEMO_SECTIONS = [
    "Company snapshot",
    "Investment hypotheses",
    "SWOT",
    "Team & history",
    "Problem & product",
    "Technology & defensibility",
    "Market sizing",
    "Competition",
    "Traction & KPIs",
    "Financials & round structure",
    "Cap table",
    "Due diligence log",
    "Exit perspective",
]

MEMO_SECTION_GUIDANCE = {
    "Company snapshot": (
        "One-paragraph 'in a nutshell': market size, the structural problem, why it's urgent, "
        "and how the product solves it."
    ),
    "Investment hypotheses": (
        "Explicit 'why we want to invest' bullets — team quality, market wedge, stickiness / "
        "retention mechanics, traction signal, defensibility, expansion path."
    ),
    "SWOT": (
        "Strengths, weaknesses, opportunities, risks — each as short, evidence-backed bullets "
        "(label S/W/O/T clearly)."
    ),
    "Team & history": (
        "Founder background, exec team pedigree, why the fund is comfortable with any red flags "
        "(e.g. single-founder, first-time founder with thin public footprint), company timeline "
        "from founding to today. Cold-start founders: score from domain depth, building-in-public, "
        "iteration cadence — do not invent GitHub/funding history."
    ),
    "Problem & product": (
        "The core problem(s) in plain language, then the step-by-step product / process solving it."
    ),
    "Technology & defensibility": (
        "What's proprietary vs. commoditizable, the data moat, model / architecture choices, "
        "why the advantage compounds over time."
    ),
    "Market sizing": (
        "Top-down and/or bottom-up TAM / SAM / SOM, with assumptions stated explicitly."
    ),
    "Competition": (
        "Named competitor clusters, how each differs from the company, and who could become a "
        "threat later."
    ),
    "Traction & KPIs": (
        "Customer count, ARR / revenue, growth trajectory, unit economics (CAC, sales cycle, churn), "
        "usage metrics (e.g. DAU). Only numbers present in evidence."
    ),
    "Financials & round structure": (
        "Historical + projected P&L (revenue, EBITDA, opex, COGS), round size, runway, next-round timing."
    ),
    "Cap table": (
        "Pre- and post-round ownership by party, dilution assumptions, VSOP allocation."
    ),
    "Due diligence log": (
        "What was checked (commercial, people, financial, legal, technical), what's still open."
    ),
    "Exit perspective": (
        "Plausible exit paths (strategic acquirers, PE roll-up, category comparables) and why "
        "they'd pay a premium."
    ),
}


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


def _gap_flags(title: str, content: str | None) -> tuple[str | None, bool]:
    """Return (content, not_disclosed). Founder-sensitive empties are withheld;
    analyst-section empties are insufficient evidence (not_disclosed=false)."""
    if content:
        return content, False
    return None, title in FOUNDER_SENSITIVE_SECTIONS


def _normalize_memo_sections(raw_sections: list[dict] | None) -> list[dict]:
    """Force canonical 13-section order; unknown titles dropped; gaps flagged."""
    by_title: dict[str, dict] = {}
    for s in raw_sections or []:
        if not isinstance(s, dict):
            continue
        title = (s.get("title") or "").strip()
        if title not in ALL_MEMO_SECTIONS:
            # Allow minor title variants
            for canonical in ALL_MEMO_SECTIONS:
                if title.lower() == canonical.lower():
                    title = canonical
                    break
            else:
                continue
        content = s.get("content")
        if isinstance(content, str):
            stripped = content.strip()
            if stripped.lower() in {
                "not_disclosed",
                "not_disclosed=true",
                "null",
                "none",
                "n/a",
                "unavailable",
                "unavailable at this stage.",
            }:
                content = None
            else:
                content = stripped or None
        else:
            content = None
        # LLM may stamp not_disclosed on SWOT/hypotheses/exit — override by section type.
        content, undisclosed = _gap_flags(title, content)
        by_title[title] = {
            "title": title,
            "content": content,
            "not_disclosed": undisclosed,
            "required": title in REQUIRED_MEMO_SECTIONS,
        }

    out = []
    for title in ALL_MEMO_SECTIONS:
        if title in by_title:
            out.append(by_title[title])
        else:
            _, undisclosed = _gap_flags(title, None)
            out.append({
                "title": title,
                "content": None,
                "not_disclosed": undisclosed,
                "required": title in REQUIRED_MEMO_SECTIONS,
            })
    return out


def _heuristic_referee(
    company_name: str,
    claims: list[dict],
    analyst_out: dict,
    research_blob: str = "",
    *,
    founder_name: str = "",
) -> dict:
    has_traction_claim = any(
        any(k in c.get("text", "").lower() for k in ("traction", "arr", "customers", "users", "raised", "revenue"))
        or "$" in c.get("text", "")
        for c in claims
    )
    claim_texts = [c.get("text", "") for c in claims if c.get("text")]
    snapshot_bits = [f"{company_name} — {len(claims)} research/deck claim(s)."]
    if research_blob:
        snapshot_bits.append(research_blob[:400].replace("\n", " "))

    traction = next(
        (
            c
            for c in claim_texts
            if any(k in c.lower() for k in ("$", "raised", "arr", "customers", "users", "funding", "revenue"))
        ),
        None,
    ) if has_traction_claim else None

    team_bits = []
    if founder_name:
        team_bits.append(f"Founder: {founder_name}.")
    for c in claim_texts:
        if any(k in c.lower() for k in ("founder", "ceo", "team", "previously", "ex-", "alumni")):
            team_bits.append(c)
            break

    dd_bits = [
        "Commercial: public web / deck claims reviewed.",
        "People: founder signals from research dossier (if present).",
        "Financial / legal / technical deep-dive: still open — not in source pack.",
    ]

    has_signal = bool(claim_texts or (research_blob or "").strip())
    hypotheses = None
    swot = None
    exit_view = None
    if has_signal:
        wedge = claim_texts[0] if claim_texts else research_blob[:240].replace("\n", " ").strip()
        hypotheses = (
            f"• Product / market wedge: {wedge}\n"
            f"• Team: {founder_name or 'public pedigree signals'} — diligence continues on domain fit.\n"
            "• Traction / stickiness / defensibility: only what is evidenced in the source pack; "
            "do not assume retention or moat beyond cited claims."
        )
        strengths = claim_texts[:2] or [research_blob[:180].replace("\n", " ").strip()]
        swot = (
            "Strengths:\n- "
            + "\n- ".join(strengths)
            + "\nWeaknesses:\n- Limited disclosed financials / unit economics in the source pack.\n"
            "Opportunities:\n- Category expansion if product-market fit holds.\n"
            "Threats / risks:\n- Competitive response; evidence gaps on retention and pricing power."
        )
        exit_view = (
            f"Primary path for {company_name}: strategic acquisition by an incumbent serving the "
            "same buyers, once category position and retention are clearer. Secondary: growth equity "
            "/ PE only if recurring revenue scales — not yet evidenced enough to underwrite. "
            "Specific acquirer names and premiums need more comps than the source pack provides."
        )

    draft = [
        {"title": "Company snapshot", "content": " ".join(snapshot_bits)[:700], "not_disclosed": False},
        {"title": "Investment hypotheses", "content": hypotheses, "not_disclosed": False},
        {"title": "SWOT", "content": swot, "not_disclosed": False},
        {
            "title": "Team & history",
            "content": " ".join(team_bits)[:500] if team_bits else None,
            "not_disclosed": False,
        },
        {
            "title": "Problem & product",
            "content": claim_texts[0] if claim_texts else None,
            "not_disclosed": False,
        },
        {"title": "Technology & defensibility", "content": None, "not_disclosed": False},
        {"title": "Market sizing", "content": None, "not_disclosed": False},
        {"title": "Competition", "content": None, "not_disclosed": False},
        {"title": "Traction & KPIs", "content": traction, "not_disclosed": False},
        {"title": "Financials & round structure", "content": None, "not_disclosed": True},
        {"title": "Cap table", "content": None, "not_disclosed": True},
        {
            "title": "Due diligence log",
            "content": "\n".join(f"- {b}" for b in dd_bits),
            "not_disclosed": False,
        },
        {"title": "Exit perspective", "content": exit_view, "not_disclosed": False},
    ]
    return {
        "sections": _normalize_memo_sections(draft),
        "axis_scores": analyst_out["axis_scores"],
        "prompt_version": "heuristic-referee-v4",
    }


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

    guidance_block = "\n".join(
        f"- {title}{' [REQUIRED]' if title in REQUIRED_MEMO_SECTIONS else ' [optional]'}: {MEMO_SECTION_GUIDANCE[title]}"
        for title in ALL_MEMO_SECTIONS
    )
    sections_json = ",\n".join(
        f'  {{"title": "{title}", "content": <string or null>, "not_disclosed": <bool>}}'
        for title in ALL_MEMO_SECTIONS
    )

    system = (
        "You are the Referee in a VC diligence pipeline. Write a full investment memo that "
        "matches the Maschmeyer Group / Hack-Nation memo appendix — every section listed below "
        "MUST appear in the JSON array, in that order.\n\n"
        f"SECTION SPECS:\n{guidance_block}\n\n"
        "HARD RULES:\n"
        "1. REQUIRED sections (Company snapshot, Investment hypotheses, SWOT, Problem & product, "
        "Traction & KPIs): SYNTHESIZE from the research dossier + claims. These are analyst "
        "sections — founders rarely put 'Investment hypotheses' or 'SWOT' in a pitch deck. "
        "Write them from evidence. Only use content=null when the dossier has essentially "
        "nothing about the company. Set not_disclosed=false for these.\n"
        "2. Exit perspective, Competition, Market sizing, Technology & defensibility: likewise "
        "analyst synthesis. Prefer cautious category-level exit paths / competitor clusters "
        "from the dossier over leaving them empty. content=null + not_disclosed=false if "
        "truly no signal — never claim the founder 'withheld' a SWOT or exit strategy.\n"
        "3. ONLY Financials & round structure and Cap table use not_disclosed=true when "
        "missing — those are confidential founder-pack items. NEVER invent ARR, customers, "
        "funding, cap table %, P&L, or TAM figures.\n"
        "4. Validator 'contradicted' claims must be flagged in the relevant section, not presented as fact.\n"
        "5. Be brief — short bullets, no padding. SWOT must label Strengths / Weaknesses / "
        "Opportunities / Threats.\n"
        "6. Team & history: for first-time / cold-start founders with thin GitHub/funding/network, "
        "state what IS known (domain depth, iteration, public building) and note unknowns — "
        "do not invent pedigree.\n"
        "7. Due diligence log: list what this pipeline actually checked vs still open.\n\n"
        "Return strict JSON:\n"
        '{"sections": [\n'
        f"{sections_json}\n"
        "]}"
    )
    user = (
        f"Company: {company_name}\nFounder: {founder_name or 'unknown'}\n\n"
        f"LIVE RESEARCH DOSSIER:\n{research_block}\n\n"
        f"Claims + validator verdicts:\n{claims_block}\n\n"
        f"Analyst axis scores (independent — do not average):\n{axis_block}"
    )
    data = llm.chat_json(system, user)
    if not data or "sections" not in data:
        return None

    sections = _normalize_memo_sections(data.get("sections"))
    return {
        "sections": sections,
        "axis_scores": analyst_out["axis_scores"],
        "prompt_version": f"openai:{llm.MODEL}:referee-v4",
    }


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
    return _heuristic_referee(
        company_name,
        claims,
        analyst_out,
        research_blob=research_blob,
        founder_name=founder_name,
    )


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
