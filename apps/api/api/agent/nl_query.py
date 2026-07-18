"""`POST /query/natural-language` (`docs/05-CURSOR-SKILLS.md` §3): one-pass
resolution of a compound query (e.g. "technical founder, Berlin, AI infra,
enterprise traction, no prior VC backing") into structured constraints,
then a ranked result set with a per-clause match explanation for every
opportunity — never a single opaque relevance score.
"""

from __future__ import annotations

from typing import Any

from api.core import opportunity_store
from api.intelligence import llm


def _decompose_llm(query: str) -> list[str] | None:
    system = (
        "Decompose a venture-capital natural-language search query into a list of short, "
        "independent constraints (sector, geography, stage, traction signal, team background, "
        "funding history, etc). Keep each constraint to a few words. "
        'Return strict JSON: {"constraints": ["...", "..."]}'
    )
    data = llm.chat_json(system, query)
    if not data or not isinstance(data.get("constraints"), list):
        return None
    constraints = [c.strip() for c in data["constraints"] if isinstance(c, str) and c.strip()]
    return constraints or None


def _decompose_heuristic(query: str) -> list[str]:
    return [part.strip() for part in query.replace(";", ",").split(",") if part.strip()]


def _opportunity_text(opp: dict[str, Any]) -> str:
    parts = [
        opp.get("company_name", ""),
        opp.get("company_sector", "") or "",
        opp.get("founder_name", ""),
        opp.get("discovery_channel", "") or "",
        opp.get("source", ""),
        opp.get("triggering_signal", "") or "",
    ]
    for aff in opp.get("founder_domain_affinity", []) or []:
        if isinstance(aff, dict) and aff.get("sector"):
            parts.append(aff["sector"])
    for c in opp.get("claims", []) or []:
        parts.append(c.get("text", ""))
    memo = opp.get("memo") or {}
    for section in memo.get("sections", []) or []:
        if section.get("content"):
            parts.append(section["content"])
    return " ".join(p for p in parts if p)


def _match_llm(opp_text: str, constraints: list[str]) -> list[dict[str, Any]] | None:
    system = (
        "You are grading whether a startup opportunity matches each search constraint. Use ONLY "
        "the opportunity text given — if it doesn't mention something, the constraint is NOT matched, "
        "never assume. Return strict JSON: "
        '{"clause_matches": [{"constraint": "...", "matched": true|false, "explanation": "short reason"}]}'
    )
    user = f"Opportunity text:\n{opp_text or '(no text available)'}\n\nConstraints:\n" + "\n".join(f"- {c}" for c in constraints)
    data = llm.chat_json(system, user)
    if not data or not isinstance(data.get("clause_matches"), list):
        return None
    matches = []
    for m in data["clause_matches"]:
        if not isinstance(m, dict) or "constraint" not in m:
            continue
        matches.append({
            "constraint": m["constraint"],
            "matched": bool(m.get("matched", False)),
            "explanation": m.get("explanation", ""),
        })
    return matches or None


def _match_heuristic(opp_text: str, constraints: list[str]) -> list[dict[str, Any]]:
    haystack = opp_text.lower()
    matches = []
    for c in constraints:
        keywords = [w.strip(".,()") for w in c.lower().split() if len(w) > 3]
        hit = any(k in haystack for k in keywords) if keywords else False
        matches.append({
            "constraint": c,
            "matched": hit,
            "explanation": "Keyword match on available text." if hit else "No keyword overlap found — may still be a real gap in available data, not necessarily a non-match.",
        })
    return matches


def run(query: str) -> dict[str, Any]:
    constraints = _decompose_llm(query) if llm.is_available() else None
    decompose_mode = f"openai:{llm.MODEL}:decompose-v1" if constraints else "heuristic-split-v1"
    if constraints is None:
        constraints = _decompose_heuristic(query)

    summaries = opportunity_store.list_opportunities()
    results = []
    for summary in summaries:
        full = opportunity_store.get_opportunity(summary["id"]) or summary
        opp_text = _opportunity_text(full)

        clause_matches = _match_llm(opp_text, constraints) if llm.is_available() else None
        match_mode = f"openai:{llm.MODEL}:match-v1" if clause_matches else "heuristic-keyword-v1"
        if clause_matches is None:
            clause_matches = _match_heuristic(opp_text, constraints)

        match_count = sum(1 for m in clause_matches if m["matched"])
        results.append({
            "opportunity_id": summary["id"],
            "company_name": summary.get("company_name"),
            "company_sector": full.get("company_sector"),
            "founder_name": summary.get("founder_name"),
            "match_count": match_count,
            "match_ratio": round(match_count / len(constraints), 2) if constraints else 0.0,
            "clause_matches": clause_matches,
            "match_mode": match_mode,
        })

    results.sort(key=lambda r: r["match_count"], reverse=True)
    return {"query": query, "constraints": constraints, "decompose_mode": decompose_mode, "results": results}
