"""Watchlist state machine (`docs/03-SOURCING.md` §3-4):

    discovered -> scored -> activation-candidate -> outreach-sent -> applied -> screening

Promotion requires the conviction score to cross the active thesis's
threshold AND multiple independent corroborating signals — a single
strong signal stays on the watchlist. Activation converges into the
exact same `opportunity_store.create_opportunity` code path used by
native inbound applications (§3 "Convergence").
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from api.agent import perplexity, thesis_store
from api.core import opportunity_store
from api.core.db import get_client
from api.ingestion import fast_screen, memory, outbound_enrich
from api.ingestion.connectors import arxiv, github, hackernews, linkedin
from api.intelligence import retrieval

_MEMORY: dict[str, dict[str, Any]] = {}

_GITHUB_URL_RE = re.compile(r"github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)
_GITHUB_URL_BLOCKLIST = {"features", "about", "pricing", "topics", "sponsors", "orgs", "marketplace", "collections"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Cold-start-aware conviction scoring
# ---------------------------------------------------------------------------


def _score_signals(signals: list[dict[str, Any]]) -> tuple[float | None, float, str]:
    """Returns (conviction_score, confidence, rationale). No signals is
    `unknown` (None), never a low/bad score — absence of evidence is not
    evidence of absence (`docs/00-OVERVIEW.md` §4 rule 3/6)."""
    if not signals:
        return None, 0.15, "No public footprint found on any connector yet — cold start, unscored rather than penalized."

    weighted_total = 0.0
    weight_sum = 0.0
    parts = []
    for s in signals:
        if s["channel"] == "github":
            gh_score = min(1.0, (s.get("total_stars", 0) / 200) * 0.5 + (s.get("repos_pushed_last_90d", 0) / 5) * 0.5)
            weighted_total += gh_score * 0.4
            weight_sum += 0.4
            parts.append(f"GitHub: {s.get('own_repo_count', 0)} repos, {s.get('total_stars', 0)} stars, {s.get('repos_pushed_last_90d', 0)} pushed in last 90d")
        elif s["channel"] == "hackernews":
            hn_score = min(1.0, s.get("total_points", 0) / 200)
            weighted_total += hn_score * 0.25
            weight_sum += 0.25
            parts.append(f"HN: {s.get('story_count', 0)} stories, {s.get('total_points', 0)} points, top: {s.get('top_story_title')!r}")
        elif s["channel"] == "perplexity":
            ev_count = len(s.get("evidence", []))
            pplx_score = min(1.0, ev_count / 5)
            weighted_total += pplx_score * 0.2
            weight_sum += 0.2
            parts.append(f"Perplexity research: {ev_count} corroborating source(s)")
        elif s["channel"] == "web_search":
            result_count = len(s.get("results", []))
            web_score = min(1.0, result_count / 3)
            weighted_total += web_score * 0.15
            weight_sum += 0.15
            parts.append(f"Tavily web search: {result_count} independent result(s)")
        elif s["channel"] == "arxiv":
            paper_count = s.get("paper_count", 0)
            arxiv_score = min(1.0, paper_count / 3)
            weighted_total += arxiv_score * 0.15
            weight_sum += 0.15
            parts.append(f"arXiv: {paper_count} paper(s), top: {s.get('top_title')!r}")
        elif s["channel"] == "linkedin":
            # A resolved public profile is a strong identity/public-footprint
            # signal; snippet richness adds a little, never fabricates merit.
            li_score = 0.55 if s.get("profile_url") else 0.0
            li_score += min(0.35, (s.get("result_count") or 0) * 0.1)
            if s.get("snippet"):
                li_score = min(1.0, li_score + 0.1)
            weighted_total += li_score * 0.2
            weight_sum += 0.2
            parts.append(
                f"LinkedIn: {s.get('profile_url') or 'no profile URL'} "
                f"({s.get('result_count', 0)} public hit(s))"
            )

    conviction = round(weighted_total / weight_sum, 2) if weight_sum else None
    confidence = round(min(0.9, 0.3 + 0.3 * len(signals)), 2)
    rationale = "; ".join(parts) if parts else "Signal found but not enough structure to score confidently."
    return conviction, confidence, rationale


# ---------------------------------------------------------------------------
# CRUD (Supabase-backed, in-memory fallback)
# ---------------------------------------------------------------------------


def _row_out(row: dict[str, Any], founder_name: str, company_name: str | None) -> dict[str, Any]:
    return {
        "id": row["id"],
        "founder_id": row["founder_id"],
        "founder_name": founder_name,
        "company_id": row.get("company_id"),
        "company_name": company_name,
        "stage": row["stage"],
        "conviction_score": row.get("conviction_score"),
        "promoted_via": row.get("promoted_via"),
        "signals": row.get("signals", []),
        "triggering_signal": row.get("triggering_signal"),
        "opportunity_id": row.get("opportunity_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def list_watchlist() -> list[dict[str, Any]]:
    client = get_client()
    if client is None:
        return [_row_out(r, r["_founder_name"], r.get("_company_name")) for r in _MEMORY.values()]
    res = (
        client.table("watchlist_entries")
        .select("*, founders(display_name), companies(name)")
        .order("created_at", desc=True)
        .execute()
    )
    return [
        _row_out(r, (r.get("founders") or {}).get("display_name", "Unknown"), (r.get("companies") or {}).get("name"))
        for r in res.data
    ]


def get_entry(entry_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        r = _MEMORY.get(entry_id)
        return _row_out(r, r["_founder_name"], r.get("_company_name")) if r else None
    res = (
        client.table("watchlist_entries")
        .select("*, founders(display_name), companies(name)")
        .eq("id", entry_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    r = res.data[0]
    return _row_out(r, (r.get("founders") or {}).get("display_name", "Unknown"), (r.get("companies") or {}).get("name"))


def _update_entry(entry_id: str, **fields: Any) -> None:
    client = get_client()
    if client is None:
        _MEMORY[entry_id].update(fields)
        return
    client.table("watchlist_entries").update({**fields, "updated_at": _now_iso()}).eq("id", entry_id).execute()


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


def _extract_github_username(text: str) -> str | None:
    for match in _GITHUB_URL_RE.finditer(text or ""):
        login = match.group(1)
        if login.lower() not in _GITHUB_URL_BLOCKLIST:
            return login
    return None


def discover(
    founder_name: str,
    *,
    company_name: str | None = None,
    github_username: str | None = None,
    hn_query: str | None = None,
    linkedin_url: str | None = None,
) -> dict[str, Any]:
    """Runs connectors + live research, resolves identity, and creates a
    `scored` watchlist entry in one call (discover -> scored is cheap
    enough to collapse into a single request for the demo).

    Signal stack: GitHub, Hacker News, arXiv, LinkedIn (public web),
    Perplexity, Tavily. Research lands in Bronze as provenance-tagged
    raw events — watchlist corroboration, not pre-trusted facts.
    """
    research_query = (
        f"Who is {founder_name}"
        + (f", founder of {company_name}" if company_name else "")
        + "? Company overview, funding, background, public GitHub, and LinkedIn profile URL."
    )

    # Perplexity first — often surfaces GitHub / LinkedIn handles when the
    # caller didn't supply them, and always gives citable research.
    pplx = perplexity.research(research_query)
    if pplx:
        blob = pplx["answer"] + " " + " ".join(pplx.get("citations", []))
        if not github_username:
            github_username = _extract_github_username(blob)
        if not linkedin_url:
            linkedin_url = linkedin.extract_profile_url_from_text(blob)

    founder = memory.resolve_founder(
        founder_name,
        source="github" if github_username else None,
        source_entity_id=github_username,
    )
    company = memory.resolve_company(company_name) if company_name else None

    signals: list[dict[str, Any]] = []

    gh = github.fetch_profile_signals(github_username) if github_username else None
    if gh:
        signals.append({"channel": "github", **gh})

    hn = hackernews.fetch_launch_signals(hn_query or company_name or founder_name)
    if hn:
        signals.append({"channel": "hackernews", **hn})

    ax = arxiv.fetch_paper_signals(f"{founder_name} {company_name or ''}".strip())
    if ax:
        signals.append(ax if ax.get("channel") else {"channel": "arxiv", **ax})

    li = linkedin.fetch_profile_signals(
        founder_name,
        company_name=company_name,
        linkedin_url=linkedin_url,
    )
    if li:
        signals.append(li)

    if pplx:
        bronze = memory.ingest_raw(
            "perplexity",
            {"query": research_query, "answer": pplx["answer"], "citations": pplx["citations"]},
            entity_type="founder_research",
            source_entity_id=founder_name,
        )
        signals.append({
            "channel": "perplexity",
            "query": research_query,
            "answer": pplx["answer"][:1200],
            "citations": pplx["citations"][:8],
            "evidence": pplx["evidence"][:8],
            "bronze_id": bronze["id"],
        })

    web_query = f"{founder_name} {company_name or ''} founder".strip()
    web_results = retrieval.search(web_query, max_results=5)
    if web_results:
        bronze = memory.ingest_raw(
            "tavily",
            {"query": web_query, "results": web_results},
            entity_type="founder_web_search",
            source_entity_id=founder_name,
        )
        signals.append({
            "channel": "web_search",
            "query": web_query,
            "results": web_results,
            "bronze_id": bronze["id"],
        })

    conviction_score, confidence, rationale = _score_signals(signals)
    stage = "scored" if signals else "discovered"
    primary_source = (
        "github" if github_username
        else "linkedin" if li
        else "perplexity" if pplx
        else "tavily" if web_results
        else "hackernews"
    )

    client = get_client()
    if client is None:
        entry_id = f"watchlist-{uuid.uuid4().hex[:8]}"
        row = {
            "id": entry_id,
            "founder_id": founder["id"],
            "company_id": company["id"] if company else None,
            "stage": stage,
            "conviction_score": conviction_score,
            "signals": signals,
            "source": primary_source,
            "source_entity_id": github_username or hn_query or founder_name,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "_founder_name": founder_name,
            "_company_name": company_name,
        }
        _MEMORY[entry_id] = row
        out = _row_out(row, founder_name, company_name)
    else:
        row = {
            "founder_id": founder["id"],
            "company_id": company["id"] if company else None,
            "stage": stage,
            "conviction_score": conviction_score,
            "signals": signals,
            "source": primary_source,
            "source_entity_id": github_username or hn_query or founder_name,
        }
        created = client.table("watchlist_entries").insert(row).execute().data[0]
        out = _row_out(created, founder_name, company_name)

    out["confidence"] = confidence
    out["rationale"] = rationale
    return out


def promote(entry_id: str) -> dict[str, Any]:
    entry = get_entry(entry_id)
    if entry is None:
        raise ValueError("Watchlist entry not found.")

    active_thesis = thesis_store.get_active_thesis()
    threshold = active_thesis["watchlist_promotion_threshold"] if active_thesis else 0.65
    signals = entry.get("signals") or []
    score = entry.get("conviction_score")

    if score is None:
        return {**entry, "promoted": False, "reason": "Cold start — no scoreable signal yet. Not penalized, just not eligible for promotion."}
    if len(signals) < 2:
        return {**entry, "promoted": False, "reason": f"Only {len(signals)} independent signal(s) found — promotion requires multi-signal corroboration (≥2)."}
    if score < threshold:
        return {**entry, "promoted": False, "reason": f"Conviction score {score} is below the active thesis's promotion threshold {threshold}."}

    channels = sorted({s["channel"] for s in signals})
    promoted_via = "multi_signal:" + "+".join(channels)
    _update_entry(entry_id, stage="activation-candidate", promoted_via=promoted_via)
    updated = get_entry(entry_id)
    return {**updated, "promoted": True, "reason": f"Conviction {score} ≥ threshold {threshold} with {len(signals)} corroborating signals ({', '.join(channels)})."}


def generate_outreach(entry_id: str) -> dict[str, Any]:
    entry = get_entry(entry_id)
    if entry is None:
        raise ValueError("Watchlist entry not found.")
    if entry["stage"] != "activation-candidate":
        raise ValueError(f"Entry must be 'activation-candidate' before outreach (currently '{entry['stage']}').")

    signals = entry.get("signals") or []
    top_signal = max(signals, key=lambda s: s.get("total_stars", 0) + s.get("total_points", 0)) if signals else None
    if top_signal and top_signal["channel"] == "github":
        trigger_summary = f"GitHub activity ({top_signal.get('total_stars', 0)} stars, {top_signal.get('repos_pushed_last_90d', 0)} repos pushed in 90d)"
        draft = (
            f"Hi {entry['founder_name']},\n\n"
            f"I came across your GitHub profile ({top_signal.get('profile_url', '')}) — the pace of shipping "
            f"({top_signal.get('repos_pushed_last_90d', 0)} repos pushed in the last 90 days, "
            f"{top_signal.get('total_stars', 0)} stars) caught our attention.\n\n"
            f"We invest in {entry['company_name'] or 'early-stage teams'} at the pre-seed/seed stage. "
            f"Open to a 20-minute call this week?\n\n— VC Brain"
        )
    elif top_signal and top_signal["channel"] == "hackernews":
        trigger_summary = f"HN traction ({top_signal.get('total_points', 0)} points on {top_signal.get('top_story_title')!r})"
        draft = (
            f"Hi {entry['founder_name']},\n\n"
            f"Saw the Hacker News discussion on {top_signal.get('top_story_title')!r} "
            f"({top_signal.get('top_story_points', 0)} points) — congrats on the traction.\n\n"
            f"We invest in {entry['company_name'] or 'early-stage teams'} at the pre-seed/seed stage. "
            f"Open to a 20-minute call this week?\n\n— VC Brain"
        )
    else:
        trigger_summary = "multi-signal corroboration"
        draft = f"Hi {entry['founder_name']},\n\nWe've been tracking your work and would love to connect.\n\n— VC Brain"

    _update_entry(entry_id, stage="outreach-sent", triggering_signal=trigger_summary)
    updated = get_entry(entry_id)
    return {**updated, "draft": draft}


def _submit_outbound_application(entry: dict[str, Any]) -> dict[str, Any]:
    """Same shape as `POST /application/submit`: extract claims → create
    opportunity → fast screen → persist claims. Research becomes provisional
    claims (source=outbound_research), never fabricated beyond the text.

    If the company already has an open opportunity, attach (reuse id) and skip
    re-research / re-screen — diligence refresh stays on Analyze.
    """
    signals = entry.get("signals") or []
    company_name = entry["company_name"] or f"{entry['founder_name']}'s company"
    founder_name = entry["founder_name"]
    # Persist every connector channel (comma-separated) so outbound cards can
    # show "sources extracted from" without another round-trip.
    channels: list[str] = []
    for s in signals:
        ch = (s.get("channel") or "").strip()
        if ch and ch not in channels:
            channels.append(ch)
    primary_channel = ",".join(channels) if channels else "outbound"

    # Resolve early so we can short-circuit before expensive claim extraction.
    company = memory.resolve_company(company_name, source="outbound")
    open_opp = opportunity_store.find_open_opportunity(company["id"])
    if open_opp is not None:
        dedupe = {
            "action": "attached",
            "reason": "open_opportunity_exists",
            "prior_status": open_opp.get("status"),
            "prior_source": open_opp.get("source"),
            "deferred": ["outbound_research", "fast_screen", "analyze"],
        }
        return {
            "opportunity_id": open_opp["id"],
            "company_id": company["id"],
            "claims_extracted": 0,
            "screen_verdict": open_opp.get("screen_verdict") or "needs-more-info",
            "screen_reason": (
                "Company already has an open opportunity — skipped re-research; "
                "run Analyze to refresh."
            ),
            "sector": company.get("sector"),
            "dedupe": dedupe,
        }

    claims = outbound_enrich.claims_from_signals(
        signals, founder_name=founder_name, company_name=company_name
    )
    sector = outbound_enrich.sector_from_signals(
        signals, company_name=company_name, founder_name=founder_name
    )
    if sector:
        memory.resolve_company(company_name, sector=sector, source="outbound")

    verdict, reason = fast_screen.screen(company_name, claims)
    # Outbound research claims are first-class for screening — if we extracted
    # any, treat as pass even when the heuristic wanted needs-more-info for
    # "empty deck" (that rule is inbound-deck-centric).
    if claims and verdict == "needs-more-info":
        verdict, reason = "pass", f"Outbound research yielded {len(claims)} provisional claims — proceeding to 3-axis analysis."

    opp = opportunity_store.create_opportunity(
        company_name=company_name,
        founder_name=founder_name,
        source="outbound",
        discovery_channel=primary_channel,
        triggering_signal=entry.get("triggering_signal") or entry.get("promoted_via"),
    )
    # Tag claims with outbound source so Trust/Validator treat them as research
    # assertions, not deck slides — update_opportunity still inserts claim rows.
    claim_rows = [
        {**c, "claim_id": f"claim-{i}", "source": "outbound_research"}
        for i, c in enumerate(claims)
    ]
    opportunity_store.update_opportunity(
        opp["id"],
        claims=claim_rows,
        screen_verdict=verdict,
        status="screening" if verdict == "pass" else "rejected" if verdict == "reject" else "needs-more-info",
    )
    opportunity_store.set_sla_stage(opp["id"], "screening_at")
    return {
        "opportunity_id": opp["id"],
        "company_id": opp.get("company_id") or company["id"],
        "claims_extracted": len(claims),
        "screen_verdict": verdict,
        "screen_reason": reason,
        "sector": sector,
        "dedupe": opp.get("dedupe") or {"action": "created"},
    }


def activate(entry_id: str) -> dict[str, Any]:
    """Convergence: activated watchlist entry enters the SAME application
    + screening path as inbound (`docs/03-SOURCING.md` §3)."""
    entry = get_entry(entry_id)
    if entry is None:
        raise ValueError("Watchlist entry not found.")
    if entry["stage"] not in {"activation-candidate", "outreach-sent", "screening"}:
        raise ValueError(
            f"Entry must be 'activation-candidate', 'outreach-sent', or re-enrichable "
            f"'screening' to activate (currently '{entry['stage']}')."
        )

    # Re-enrich path: prior activate left an empty shell — create a fresh
    # opportunity with research claims rather than leaving the dead one.
    result = _submit_outbound_application(entry)
    _update_entry(entry_id, stage="screening", opportunity_id=result["opportunity_id"])
    updated = get_entry(entry_id)
    return {**updated, **result}


def ingest_sweep_lead(
    founder_name: str,
    company_name: str,
    *,
    answer: str,
    citations: list[str],
    evidence: list[dict[str, Any]],
    bronze_id: str | None = None,
) -> dict[str, Any]:
    """Land a thesis-sweep candidate on the watchlist without re-paying for
    a full Perplexity discover — attaches the sweep answer as the perplexity
    signal, then runs Tavily + light connectors for corroboration."""
    founder = memory.resolve_founder(founder_name)
    company = memory.resolve_company(company_name)

    signals: list[dict[str, Any]] = [{
        "channel": "perplexity",
        "query": f"thesis-sourcing-sweep:{company_name}",
        "answer": answer[:1200],
        "citations": citations[:8],
        "evidence": evidence[:8],
        "bronze_id": bronze_id,
    }]

    web_query = f"{founder_name} {company_name} founder"
    web_results = retrieval.search(web_query, max_results=5)
    if web_results:
        bronze = memory.ingest_raw(
            "tavily",
            {"query": web_query, "results": web_results},
            entity_type="founder_web_search",
            source_entity_id=founder_name,
        )
        signals.append({
            "channel": "web_search",
            "query": web_query,
            "results": web_results,
            "bronze_id": bronze["id"],
        })

    hn = hackernews.fetch_launch_signals(company_name)
    if hn:
        signals.append({"channel": "hackernews", **hn})

    li_url = linkedin.extract_profile_url_from_text(
        answer + " " + " ".join(citations)
    )
    li = linkedin.fetch_profile_signals(
        founder_name,
        company_name=company_name,
        linkedin_url=li_url,
    )
    if li:
        signals.append(li)

    conviction_score, confidence, rationale = _score_signals(signals)
    stage = "scored" if signals else "discovered"

    client = get_client()
    row = {
        "founder_id": founder["id"],
        "company_id": company["id"],
        "stage": stage,
        "conviction_score": conviction_score,
        "signals": signals,
        "source": "perplexity",
        "source_entity_id": company_name,
    }
    if client is None:
        entry_id = f"watchlist-{uuid.uuid4().hex[:8]}"
        mem = {**row, "id": entry_id, "created_at": _now_iso(), "updated_at": _now_iso(),
               "_founder_name": founder_name, "_company_name": company_name}
        _MEMORY[entry_id] = mem
        out = _row_out(mem, founder_name, company_name)
    else:
        created = client.table("watchlist_entries").insert(row).execute().data[0]
        out = _row_out(created, founder_name, company_name)
    out["confidence"] = confidence
    out["rationale"] = rationale
    return out
