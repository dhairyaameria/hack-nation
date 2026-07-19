"""Outbound → inbound convergence helpers (`docs/03-SOURCING.md` §3).

Watchlist research (Perplexity / Tavily / connectors) is turned into
provisional claims + company context so activated leads enter the SAME
screening path as a deck application — not an empty opportunity shell.
Claims are provenance-tagged as `outbound_research`, never pre-trusted.
"""

from __future__ import annotations

import re
from typing import Any

from api.intelligence import llm


def _research_blob(signals: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for s in signals:
        ch = s.get("channel")
        if ch == "perplexity" and s.get("answer"):
            parts.append(f"[Perplexity]\n{s['answer']}")
            for url in (s.get("citations") or [])[:6]:
                parts.append(f"  cite: {url}")
        elif ch == "web_search":
            for r in (s.get("results") or [])[:5]:
                parts.append(f"[Tavily] {r.get('title', '')}: {(r.get('content') or '')[:300]} ({r.get('url', '')})")
        elif ch == "github":
            parts.append(
                f"[GitHub] @{s.get('username')} — {s.get('own_repo_count', 0)} repos, "
                f"{s.get('total_stars', 0)} stars, {s.get('repos_pushed_last_90d', 0)} pushed/90d"
            )
        elif ch == "hackernews":
            parts.append(
                f"[HN] {s.get('story_count', 0)} stories, {s.get('total_points', 0)} points — "
                f"{s.get('top_story_title', '')}"
            )
        elif ch == "arxiv":
            parts.append(
                f"[arXiv] {s.get('paper_count', 0)} papers — top: {s.get('top_title', '')}"
            )
    return "\n".join(parts)


def _heuristic_claims(blob: str, company_name: str, founder_name: str) -> list[dict[str, str]]:
    """Fallback when OpenAI is unavailable — keep factual-looking sentences."""
    claims: list[dict[str, str]] = []
    # Prefer lines / sentences that look like traction, funding, or product facts.
    chunks = re.split(r"(?<=[.!?])\s+|\n+", blob)
    keywords = (
        "raised", "funding", "arr", "revenue", "customers", "founded", "ceo",
        "co-founder", "launched", "million", "billion", "seed", "series",
        "users", "whatsapp", "remittance", "product", "platform",
    )
    for chunk in chunks:
        text = re.sub(r"\*+", "", chunk).strip()
        text = re.sub(r"^\s*[-•|]+\s*", "", text)
        if len(text) < 40 or len(text) > 280:
            continue
        if not any(k in text.lower() for k in keywords):
            continue
        if company_name.lower() not in text.lower() and founder_name.lower().split()[-1] not in text.lower():
            # Still allow strong funding/traction lines without name repeat
            if not any(k in text.lower() for k in ("raised", "arr", "customers", "funding", "series")):
                continue
        claims.append({"text": text, "slide_locator": "outbound_research"})
        if len(claims) >= 6:
            break
    if not claims and blob.strip():
        # Last resort: one snapshot claim so screening isn't empty.
        summary = re.sub(r"\s+", " ", blob)[:220].strip()
        claims.append({
            "text": f"{founder_name} / {company_name}: {summary}",
            "slide_locator": "outbound_research",
        })
    return claims


def claims_from_signals(
    signals: list[dict[str, Any]],
    *,
    founder_name: str,
    company_name: str,
) -> list[dict[str, str]]:
    blob = _research_blob(signals)
    if not blob.strip():
        return []

    if llm.is_available():
        system = (
            "Extract factual, diligence-relevant claims about a startup and founder from "
            "outbound research text. Each claim must be a single verifiable assertion "
            "(traction, funding, product, background, market). Do NOT invent facts not "
            "present in the text. Prefer specific numbers and named facts. "
            'Return strict JSON: {"claims": [{"text": "..."}], "sector": "<short sector slug or null>"}'
        )
        user = f"Founder: {founder_name}\nCompany: {company_name}\n\nResearch:\n{blob[:6000]}"
        data = llm.chat_json(system, user)
        if data and isinstance(data.get("claims"), list):
            out = []
            for c in data["claims"]:
                if isinstance(c, dict) and isinstance(c.get("text"), str) and c["text"].strip():
                    out.append({"text": c["text"].strip(), "slide_locator": "outbound_research"})
            if out:
                return out[:8]

    return _heuristic_claims(blob, company_name, founder_name)


def sector_from_signals(signals: list[dict[str, Any]], *, company_name: str, founder_name: str) -> str | None:
    blob = _research_blob(signals)
    if not blob.strip():
        return None
    if llm.is_available():
        data = llm.chat_json(
            'Infer the company\'s primary sector slug from research. '
            'Prefer one of: ai_infra, fintech, remittances, b2b_saas, devtools, crypto, healthtech, other. '
            'Return JSON: {"sector": "..."|null}',
            f"Company: {company_name}\nFounder: {founder_name}\n\n{blob[:3000]}",
        )
        if data and isinstance(data.get("sector"), str) and data["sector"].strip():
            return data["sector"].strip().lower()[:64]

    # Heuristic keyword map
    lower = blob.lower()
    for needle, sector in (
        ("remittance", "remittances"),
        ("fintech", "fintech"),
        ("whatsapp", "fintech"),
        ("stablecoin", "fintech"),
        ("ai infra", "ai_infra"),
        ("developer tool", "devtools"),
        ("devtools", "devtools"),
    ):
        if needle in lower:
            return sector
    return None


def extract_sweep_candidates(answer: str, *, max_candidates: int = 4) -> list[dict[str, str]]:
    """Parse named founder/company pairs out of a thesis-sweep Perplexity answer."""
    if not answer.strip():
        return []
    if llm.is_available():
        data = llm.chat_json(
            "Extract startup founder/company leads from research text. "
            "Only include pairs where BOTH a person name and a company name are present. "
            'Return JSON: {"candidates": [{"founder_name": "...", "company_name": "..."}]}',
            answer[:5000],
        )
        if data and isinstance(data.get("candidates"), list):
            out = []
            for c in data["candidates"]:
                if not isinstance(c, dict):
                    continue
                fn, cn = c.get("founder_name"), c.get("company_name")
                if isinstance(fn, str) and isinstance(cn, str) and fn.strip() and cn.strip():
                    out.append({"founder_name": fn.strip(), "company_name": cn.strip()})
                if len(out) >= max_candidates:
                    break
            if out:
                return out

    # Heuristic: "**Company**" lines with nearby "founded by X" — best-effort only
    return []
