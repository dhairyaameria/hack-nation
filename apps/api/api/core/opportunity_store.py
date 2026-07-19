"""Opportunities store — backed by `opportunities`, `claims`, `evidence`,
`claim_validations`, `contradiction_events`, `opportunity_axis_scores`,
`memos`, `reasoning_traces`, and `decision_log` (for SLA timestamps) when
Supabase is configured. Falls back to an in-memory store seeded from
fixtures otherwise, so the API still boots without credentials — see
`docs/16-MIGRATIONS-GUIDE.md`.

Every router (`api.ingestion.routes`, `api.intelligence.routes`) calls the
same five functions regardless of backend: `list_opportunities`,
`get_opportunity`, `create_opportunity`, `update_opportunity`,
`set_sla_stage`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from api.agent import thesis_store
from api.core import fixtures
from api.core.db import get_client
from api.ingestion import memory

# ---------------------------------------------------------------------------
# In-memory fallback (no Supabase credentials configured)
# ---------------------------------------------------------------------------

_MEMORY: dict[str, dict[str, Any]] | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_memory() -> dict[str, dict[str, Any]]:
    dashboard = fixtures.get_pipeline_dashboard()
    by_id = {o["id"]: {**o, "claims": [], "memo": None, "trace": None} for o in dashboard["opportunities"]}
    full_detail = fixtures._load("opportunity-detail")  # noqa: SLF001 — internal seed use
    if full_detail["id"] in by_id:
        by_id[full_detail["id"]].update({
            "claims": full_detail.get("claims", []),
            "memo": full_detail.get("memo"),
            "trace_id": full_detail.get("trace_id"),
        })
    return by_id


def _memory() -> dict[str, dict[str, Any]]:
    global _MEMORY
    if _MEMORY is None:
        _MEMORY = _seed_memory()
    return _MEMORY


# ---------------------------------------------------------------------------
# Supabase-backed implementation
# ---------------------------------------------------------------------------


def _sla_from_decision_log(row: dict[str, Any] | None) -> dict[str, Any]:
    row = row or {}
    return {
        "signal_at": row.get("signal_at"),
        "screening_at": row.get("screening_at"),
        "diligence_at": row.get("diligence_at"),
        "decision_at": row.get("decision_at"),
    }


def _axis_score_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "axis": row["axis"],
        "value": row["value_numeric"] if row["value_numeric"] is not None else row["value_label"],
        "trend": row["trend"],
        "confidence": row.get("confidence"),
        "evidence": row.get("evidence") or [],
    }


def _deck_fields(o: dict[str, Any]) -> dict[str, Any]:
    has_deck = bool(o.get("deck_storage_path") or o.get("deck_filename"))
    return {
        "company_id": o.get("company_id"),
        "deck_filename": o.get("deck_filename"),
        "deck_storage_path": o.get("deck_storage_path"),
        "has_deck": has_deck,
        "deck_url": f"/api/v1/inbound/applications/{o['id']}/deck" if has_deck else None,
    }


def _db_list_opportunities(client) -> list[dict[str, Any]]:
    opps_res = client.table("opportunities").select(
        "*, founders(display_name), companies(name, sector, stage, domain)"
    ).execute()
    opps = opps_res.data
    if not opps:
        return []
    ids = [o["id"] for o in opps]

    axis_res = client.table("opportunity_axis_scores").select("*").in_("opportunity_id", ids).execute()
    axis_by_opp: dict[str, list[dict[str, Any]]] = {}
    for row in axis_res.data:
        axis_by_opp.setdefault(row["opportunity_id"], []).append(_axis_score_out(row))

    decision_res = client.table("decision_log").select("*").in_("opportunity_id", ids).execute()
    decision_by_opp = {row["opportunity_id"]: row for row in decision_res.data}

    out = []
    for o in opps:
        company = o.get("companies") or {}
        out.append({
            "id": o["id"],
            "company_name": company.get("name", "Unknown"),
            "company_sector": company.get("sector"),
            "company_stage": company.get("stage"),
            "company_domain": company.get("domain"),
            "founder_name": (o.get("founders") or {}).get("display_name", "Unknown"),
            "founder_id": o["founder_id"],
            "source": o["source"],
            "discovery_channel": o.get("discovery_channel"),
            "triggering_signal": o.get("triggering_signal"),
            "screen_verdict": o.get("screen_verdict"),
            "thesis_fit_score": o.get("thesis_fit_score"),
            "status": o["status"],
            "has_contradiction": o["has_contradiction"],
            "deck_url": o.get("deck_url"),
            "deck_storage_path": o.get("deck_storage_path"),
            "deck_filename": o.get("deck_filename"),
            "inbound_rank": o.get("inbound_rank"),
            "inbound_rank_rationale": o.get("inbound_rank_rationale"),
            "inbound_ranked_at": o.get("inbound_ranked_at"),
            "axis_scores": axis_by_opp.get(o["id"], []),
            "sla": _sla_from_decision_log(decision_by_opp.get(o["id"])),
            **_deck_fields(o),
        })
    return out


def _db_get_opportunity(client, opportunity_id: str) -> dict[str, Any] | None:
    opp_res = (
        client.table("opportunities")
        .select("*, founders(display_name, domain_affinity), companies(name, sector)")
        .eq("id", opportunity_id)
        .limit(1)
        .execute()
    )
    if not opp_res.data:
        return None
    o = opp_res.data[0]

    axis_res = client.table("opportunity_axis_scores").select("*").eq("opportunity_id", opportunity_id).execute()
    axis_scores = [_axis_score_out(row) for row in axis_res.data]

    decision_res = client.table("decision_log").select("*").eq("opportunity_id", opportunity_id).limit(1).execute()
    sla = _sla_from_decision_log(decision_res.data[0] if decision_res.data else None)

    claims_res = client.table("claims").select("*").eq("opportunity_id", opportunity_id).execute()
    claim_rows = claims_res.data
    claim_ids = [c["id"] for c in claim_rows]

    validations_by_claim: dict[str, dict[str, Any]] = {}
    evidence_by_claim: dict[str, list[dict[str, Any]]] = {}
    if claim_ids:
        val_res = client.table("claim_validations").select("*").in_("claim_id", claim_ids).execute()
        validations_by_claim = {v["claim_id"]: v for v in val_res.data}

        links_res = (
            client.table("claim_evidence_links")
            .select("claim_id, relation, confidence, evidence(*)")
            .in_("claim_id", claim_ids)
            .execute()
        )
        for link in links_res.data:
            ev = link.get("evidence") or {}
            evidence_by_claim.setdefault(link["claim_id"], []).append({
                "source_type": ev.get("source_type"),
                "source_locator": ev.get("source_locator"),
                "evidence_snippet": ev.get("evidence_snippet"),
                "confidence": ev.get("confidence"),
            })

    claims_out = []
    for c in claim_rows:
        validation = validations_by_claim.get(c["id"], {})
        claims_out.append({
            "claim_id": c["id"],
            "text": c["text"],
            "slide_locator": c.get("slide_locator"),
            "source": c.get("source"),
            "trust_score": validation.get("trust_score"),
            "validation_status": validation.get("status", "unknown"),
            "evidence": evidence_by_claim.get(c["id"], []),
        })

    memo_res = client.table("memos").select("*").eq("opportunity_id", opportunity_id).limit(1).execute()
    memo = {"sections": memo_res.data[0]["sections"]} if memo_res.data else None

    company = o.get("companies") or {}
    return {
        "id": o["id"],
        "company_name": company.get("name", "Unknown"),
        "company_sector": company.get("sector"),
        "company_stage": company.get("stage"),
        "company_domain": company.get("domain"),
        "company_description": company.get("description"),
        "company_enrichment": company.get("enrichment") or {},
        "founder_name": (o.get("founders") or {}).get("display_name", "Unknown"),
        "founder_id": o["founder_id"],
        "founder_domain_affinity": (o.get("founders") or {}).get("domain_affinity") or [],
        "source": o["source"],
        "discovery_channel": o.get("discovery_channel"),
        "triggering_signal": o.get("triggering_signal"),
        "screen_verdict": o.get("screen_verdict"),
        "thesis_fit_score": o.get("thesis_fit_score"),
        "has_contradiction": o["has_contradiction"],
        "deck_url": o.get("deck_url"),
        "deck_storage_path": o.get("deck_storage_path"),
        "deck_filename": o.get("deck_filename"),
        "inbound_rank": o.get("inbound_rank"),
        "inbound_rank_rationale": o.get("inbound_rank_rationale"),
        "inbound_ranked_at": o.get("inbound_ranked_at"),
        "inbound_rank_run_id": o.get("inbound_rank_run_id"),
        "axis_scores": axis_scores,
        "claims": claims_out,
        "memo": memo,
        "trace_id": None,
        "sla": sla,
        **_deck_fields(o),
        "company_id": o.get("company_id") or company.get("id"),
    }


def list_opportunities() -> list[dict[str, Any]]:
    client = get_client()
    if client is None:
        return list(_memory().values())
    return _db_list_opportunities(client)


def list_portfolio() -> list[dict[str, Any]]:
    """Companies the fund has already funded (`status=funded` or yes decision)."""
    client = get_client()
    if client is None:
        out = []
        for opp in _memory().values():
            if opp.get("status") != "funded":
                continue
            sla = opp.get("sla") or {}
            out.append({
                "opportunity_id": opp["id"],
                "company_name": opp.get("company_name"),
                "company_sector": opp.get("company_sector"),
                "company_domain": opp.get("company_domain"),
                "founder_name": opp.get("founder_name"),
                "founder_id": opp.get("founder_id"),
                "source": opp.get("source"),
                "discovery_channel": opp.get("discovery_channel"),
                "thesis_fit_score": opp.get("thesis_fit_score"),
                "check_size_usd": opp.get("check_size_usd") or 100_000,
                "recommendation": opp.get("recommendation") or "yes",
                "funded_at": sla.get("decision_at"),
                "status": "funded",
            })
        out.sort(key=lambda r: r.get("funded_at") or "", reverse=True)
        return out

    funded_res = (
        client.table("opportunities")
        .select("*, founders(display_name), companies(name, sector, domain)")
        .eq("status", "funded")
        .execute()
    )
    opps = list(funded_res.data or [])
    seen = {o["id"] for o in opps}

    yes_res = (
        client.table("decision_log")
        .select("opportunity_id, recommendation, decision_at, confidence")
        .eq("recommendation", "yes")
        .execute()
    )
    yes_by_opp = {r["opportunity_id"]: r for r in (yes_res.data or []) if r.get("opportunity_id")}
    missing_ids = [oid for oid in yes_by_opp if oid not in seen]
    if missing_ids:
        extra = (
            client.table("opportunities")
            .select("*, founders(display_name), companies(name, sector, domain)")
            .in_("id", missing_ids)
            .execute()
        )
        opps.extend(extra.data or [])

    ids = [o["id"] for o in opps]
    decision_by_opp: dict[str, dict[str, Any]] = dict(yes_by_opp)
    if ids:
        dres = client.table("decision_log").select("*").in_("opportunity_id", ids).execute()
        for row in dres.data or []:
            decision_by_opp[row["opportunity_id"]] = row

    active = thesis_store.get_active_thesis()
    default_check = (active or {}).get("check_size_usd") or 100_000

    out = []
    for o in opps:
        d = decision_by_opp.get(o["id"]) or {}
        company = o.get("companies") or {}
        out.append({
            "opportunity_id": o["id"],
            "company_name": company.get("name", "Unknown"),
            "company_sector": company.get("sector"),
            "company_domain": company.get("domain"),
            "founder_name": (o.get("founders") or {}).get("display_name", "Unknown"),
            "founder_id": o["founder_id"],
            "source": o["source"],
            "discovery_channel": o.get("discovery_channel"),
            "thesis_fit_score": o.get("thesis_fit_score"),
            "check_size_usd": default_check,
            "recommendation": d.get("recommendation") or "yes",
            "funded_at": d.get("decision_at"),
            "status": "funded",
        })
    out.sort(key=lambda r: r.get("funded_at") or "", reverse=True)
    return out


def list_memos() -> list[dict[str, Any]]:
    """All generated investment memos with company/founder context for the
    Investment Memos index page."""
    client = get_client()
    if client is None:
        out = []
        for opp in _memory().values():
            memo = opp.get("memo")
            if not memo or not memo.get("sections"):
                continue
            sections = memo["sections"]
            filled = sum(1 for s in sections if s.get("content") and not s.get("not_disclosed"))
            gaps = sum(1 for s in sections if s.get("not_disclosed") or not s.get("content"))
            snapshot = next((s.get("content") for s in sections if s.get("title") == "Company snapshot" and s.get("content")), None)
            out.append({
                "id": f"memo-{opp['id']}",
                "opportunity_id": opp["id"],
                "company_name": opp.get("company_name"),
                "founder_name": opp.get("founder_name"),
                "source": opp.get("source"),
                "has_contradiction": opp.get("has_contradiction", False),
                "section_count": len(sections),
                "sections_filled": filled,
                "gaps_flagged": gaps,
                "snapshot": (snapshot or "")[:240] or None,
                "updated_at": None,
                "created_at": None,
            })
        return out

    res = (
        client.table("memos")
        .select("id, opportunity_id, sections, created_at, updated_at, opportunities(id, source, has_contradiction, founders(display_name), companies(name))")
        .order("updated_at", desc=True)
        .execute()
    )
    out = []
    for row in res.data or []:
        opp = row.get("opportunities") or {}
        sections = row.get("sections") or []
        filled = sum(1 for s in sections if isinstance(s, dict) and s.get("content") and not s.get("not_disclosed"))
        gaps = sum(1 for s in sections if isinstance(s, dict) and (s.get("not_disclosed") or not s.get("content")))
        snapshot = next(
            (s.get("content") for s in sections if isinstance(s, dict) and s.get("title") == "Company snapshot" and s.get("content")),
            None,
        )
        out.append({
            "id": row["id"],
            "opportunity_id": row["opportunity_id"],
            "company_name": (opp.get("companies") or {}).get("name", "Unknown"),
            "founder_name": (opp.get("founders") or {}).get("display_name", "Unknown"),
            "source": opp.get("source"),
            "has_contradiction": opp.get("has_contradiction", False),
            "section_count": len(sections),
            "sections_filled": filled,
            "gaps_flagged": gaps,
            "snapshot": (snapshot or "")[:240] or None,
            "updated_at": row.get("updated_at"),
            "created_at": row.get("created_at"),
        })
    return out


def get_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        return _memory().get(opportunity_id)
    return _db_get_opportunity(client, opportunity_id)


def create_opportunity(
    *,
    company_name: str,
    founder_name: str,
    source: str = "inbound",
    discovery_channel: str | None = "direct_apply",
    triggering_signal: str | None = None,
    deck_url: str | None = None,
    deck_storage_path: str | None = None,
    deck_filename: str | None = None,
) -> dict[str, Any]:
    client = get_client()
    if client is None:
        opp_id = f"opp-{uuid.uuid4().hex[:8]}"
        founder_id = f"founder-{uuid.uuid4().hex[:8]}"
        company_id = f"company-{uuid.uuid4().hex[:8]}"
        row = {
            "id": opp_id,
            "company_id": company_id,
            "company_name": company_name,
            "founder_name": founder_name,
            "founder_id": founder_id,
            "source": source,
            "discovery_channel": discovery_channel,
            "triggering_signal": triggering_signal,
            "screen_verdict": None,
            "thesis_fit_score": None,
            "status": "discovered",
            "has_contradiction": False,
            "deck_url": deck_url,
            "deck_storage_path": deck_storage_path,
            "deck_filename": deck_filename,
            "inbound_rank": None,
            "inbound_rank_rationale": None,
            "inbound_ranked_at": None,
            "inbound_rank_run_id": None,
            "axis_scores": [],
            "claims": [],
            "memo": None,
            "trace": None,
            "deck_filename": None,
            "deck_storage_path": None,
            "has_deck": False,
            "deck_url": None,
            "company_enrichment": {},
            "sla": {"signal_at": _now_iso(), "screening_at": None, "diligence_at": None, "decision_at": None},
        }
        _memory()[opp_id] = row
        return row

    # Resolve rather than blind-insert so the SAME real-world founder/company
    # (e.g. one already known from a prior outbound signal) isn't duplicated
    # when they later flow through this path — required for convergence
    # (docs/03-SOURCING.md §3) to actually unify identity, not just code path.
    founder = memory.resolve_founder(founder_name)
    company = memory.resolve_company(company_name)
    active_thesis = thesis_store.get_active_thesis()

    opp_row = {
        "founder_id": founder["id"],
        "company_id": company["id"],
        "thesis_profile_id": active_thesis["id"] if active_thesis else None,
        "source": source,
        "discovery_channel": discovery_channel,
        "triggering_signal": triggering_signal,
        "status": "discovered",
        "deck_url": deck_url,
        "deck_storage_path": deck_storage_path,
        "deck_filename": deck_filename,
    }
    opp = client.table("opportunities").insert(opp_row).execute().data[0]
    client.table("decision_log").insert({"opportunity_id": opp["id"], "signal_at": _now_iso()}).execute()

    return {
        "id": opp["id"],
        "company_id": company["id"],
        "company_name": company_name,
        "founder_name": founder_name,
        "founder_id": founder["id"],
        "source": source,
        "discovery_channel": discovery_channel,
        "triggering_signal": triggering_signal,
        "screen_verdict": None,
        "thesis_fit_score": None,
        "status": "discovered",
        "has_contradiction": False,
        "deck_url": deck_url,
        "deck_storage_path": deck_storage_path,
        "deck_filename": deck_filename,
        "inbound_rank": None,
        "inbound_rank_rationale": None,
        "inbound_ranked_at": None,
        "inbound_rank_run_id": None,
        "axis_scores": [],
        "claims": [],
        "memo": None,
        "trace": None,
        "deck_filename": None,
        "deck_storage_path": None,
        "has_deck": False,
        "deck_url": None,
        "sla": {"signal_at": _now_iso(), "screening_at": None, "diligence_at": None, "decision_at": None},
    }


def _db_apply_claims(client, opportunity_id: str, claims: list[dict[str, Any]]) -> None:
    if not claims:
        return
    is_analysis_output = "validation_status" in claims[0]

    if not is_analysis_output:
        # Fresh deck-parsed claims — insert rows, ignore the router's
        # placeholder claim_id (DB assigns the real one).
        rows = [
            {
                "opportunity_id": opportunity_id,
                "text": c["text"],
                "slide_locator": c.get("slide_locator"),
                "source": c.get("source") or "deck",
            }
            for c in claims
        ]
        client.table("claims").insert(rows).execute()
        return

    # Analysis output — claim_id already refers to a real row (fetched via
    # get_opportunity right before the pipeline ran). Write validations +
    # evidence, and flag contradictions.
    any_contradiction = False
    for c in claims:
        claim_id = c["claim_id"]
        client.table("claim_validations").upsert({
            "claim_id": claim_id,
            "status": c["validation_status"],
            "trust_score": c.get("trust_score"),
            "contradiction_reason": c.get("contradiction_reason"),
        }, on_conflict="claim_id").execute()

        for ev in c.get("evidence", []):
            ev_row = client.table("evidence").insert({
                "source_type": ev.get("source_type", "deck"),
                "source_locator": ev.get("source_locator", "unknown"),
                "evidence_snippet": ev.get("evidence_snippet", ""),
                "confidence": ev.get("confidence", 0.5),
            }).execute().data[0]
            client.table("claim_evidence_links").upsert({
                "claim_id": claim_id,
                "evidence_id": ev_row["id"],
                "relation": "contradicts" if c["validation_status"] == "contradicted" else "supports",
                "confidence": ev.get("confidence", 0.5),
            }, on_conflict="claim_id,evidence_id").execute()

        if c["validation_status"] == "contradicted":
            any_contradiction = True
            client.table("contradiction_events").upsert({
                "claim_id": claim_id,
                "opportunity_id": opportunity_id,
                "description": f"Claim {c.get('text', claim_id)!r} contradicted during validation.",
            }, on_conflict="claim_id").execute()

    if any_contradiction:
        client.table("opportunities").update({"has_contradiction": True}).eq("id", opportunity_id).execute()


def update_opportunity(opportunity_id: str, **fields: Any) -> dict[str, Any] | None:
    client = get_client()
    if client is None:
        row = _memory().get(opportunity_id)
        if row is None:
            return None
        row.update(fields)
        if row.get("deck_storage_path") or row.get("deck_filename"):
            row["has_deck"] = True
            row["deck_url"] = f"/api/v1/inbound/applications/{opportunity_id}/deck"
        return row

    claims = fields.pop("claims", None)
    axis_scores = fields.pop("axis_scores", None)
    memo = fields.pop("memo", None)
    trace = fields.pop("trace", None)
    fields.pop("trace_id", None)  # reasoning_traces generates its own id
    # Memory-only / computed fields — never write to opportunities table
    fields.pop("has_deck", None)
    fields.pop("deck_url", None)
    fields.pop("company_enrichment", None)
    fields.pop("company_name", None)
    fields.pop("founder_name", None)

    if claims is not None:
        _db_apply_claims(client, opportunity_id, claims)

    if axis_scores is not None:
        rows = [
            {
                "opportunity_id": opportunity_id,
                "axis": s["axis"],
                "value_numeric": s["value"] if isinstance(s["value"], (int, float)) else None,
                "value_label": s["value"] if isinstance(s["value"], str) else None,
                "trend": s.get("trend", "stable"),
                "confidence": s.get("confidence"),
                "evidence": s.get("evidence", []),
            }
            for s in axis_scores
        ]
        client.table("opportunity_axis_scores").upsert(rows, on_conflict="opportunity_id,axis").execute()

    if memo is not None:
        existing = client.table("memos").select("id").eq("opportunity_id", opportunity_id).limit(1).execute()
        if existing.data:
            client.table("memos").update({"sections": memo["sections"]}).eq("id", existing.data[0]["id"]).execute()
        else:
            client.table("memos").insert({"opportunity_id": opportunity_id, "sections": memo["sections"]}).execute()

    if trace is not None:
        rows = [
            {
                "opportunity_id": opportunity_id,
                "stage": s["stage"],
                "inputs_used": s["inputs_used"],
                "decision_rule_or_prompt_version": s["decision_rule_or_prompt_version"],
                "output_claim_ids": s["output_claim_ids"],
            }
            for s in trace["stages"]
        ]
        client.table("reasoning_traces").insert(rows).execute()

    if fields:
        try:
            client.table("opportunities").update(fields).eq("id", opportunity_id).execute()
        except Exception:
            # Older DBs may lack 011_deck_assets columns — persist non-deck fields only.
            safe = {
                k: v
                for k, v in fields.items()
                if k not in ("deck_filename", "deck_storage_path")
            }
            if safe:
                client.table("opportunities").update(safe).eq("id", opportunity_id).execute()

    return get_opportunity(opportunity_id)


def set_sla_stage(opportunity_id: str, stage: str) -> None:
    client = get_client()
    if client is None:
        row = _memory().get(opportunity_id)
        if row is not None and row.get("sla", {}).get(stage) is None:
            row.setdefault("sla", {})[stage] = _now_iso()
        return

    existing = client.table("decision_log").select("id").eq("opportunity_id", opportunity_id).limit(1).execute()
    if existing.data:
        row = client.table("decision_log").select(stage).eq("id", existing.data[0]["id"]).limit(1).execute().data[0]
        if row.get(stage) is None:
            client.table("decision_log").update({stage: _now_iso()}).eq("id", existing.data[0]["id"]).execute()
    else:
        client.table("decision_log").insert({"opportunity_id": opportunity_id, stage: _now_iso()}).execute()


def list_inbound_for_rerank() -> list[dict[str, Any]]:
    """Inbound opportunities with deck locators + claims for Perplexity rerank."""
    client = get_client()
    if client is None:
        rows = [o for o in _memory().values() if o.get("source") == "inbound"]
        return sorted(rows, key=lambda o: o.get("company_name") or "")

    opp_res = (
        client.table("opportunities")
        .select(
            "id, source, screen_verdict, status, thesis_fit_score, "
            "deck_url, deck_storage_path, deck_filename, "
            "inbound_rank, inbound_rank_rationale, inbound_ranked_at, "
            "founders(display_name), companies(name)"
        )
        .eq("source", "inbound")
        .order("created_at")
        .execute()
    )
    out: list[dict[str, Any]] = []
    for o in opp_res.data:
        claims_res = (
            client.table("claims")
            .select("id, text, slide_locator")
            .eq("opportunity_id", o["id"])
            .execute()
        )
        out.append({
            "id": o["id"],
            "company_name": (o.get("companies") or {}).get("name", "Unknown"),
            "founder_name": (o.get("founders") or {}).get("display_name", "Unknown"),
            "source": o["source"],
            "screen_verdict": o.get("screen_verdict"),
            "status": o.get("status"),
            "thesis_fit_score": o.get("thesis_fit_score"),
            "deck_url": o.get("deck_url"),
            "deck_storage_path": o.get("deck_storage_path"),
            "deck_filename": o.get("deck_filename"),
            "inbound_rank": o.get("inbound_rank"),
            "inbound_rank_rationale": o.get("inbound_rank_rationale"),
            "inbound_ranked_at": o.get("inbound_ranked_at"),
            "claims": [
                {"claim_id": c["id"], "text": c["text"], "slide_locator": c.get("slide_locator")}
                for c in claims_res.data
            ],
        })
    return out


def apply_inbound_rankings(
    rankings: list[dict[str, Any]],
    *,
    run_id: str,
    ranked_at: str,
) -> None:
    """Persist Perplexity (or heuristic) ranks onto opportunities.

    Updates `inbound_rank`, `inbound_rank_rationale`, `thesis_fit_score`,
    and run metadata. Does NOT touch the three independent axis scores.
    """
    client = get_client()
    if client is None:
        mem = _memory()
        for row in rankings:
            opp = mem.get(row["opportunity_id"])
            if opp is None:
                continue
            opp["inbound_rank"] = row["rank"]
            opp["inbound_rank_rationale"] = row.get("rationale")
            opp["thesis_fit_score"] = row.get("score")
            opp["inbound_ranked_at"] = ranked_at
            opp["inbound_rank_run_id"] = run_id
        return

    for row in rankings:
        client.table("opportunities").update({
            "inbound_rank": row["rank"],
            "inbound_rank_rationale": row.get("rationale"),
            "thesis_fit_score": row.get("score"),
            "inbound_ranked_at": ranked_at,
            "inbound_rank_run_id": run_id,
            "updated_at": ranked_at,
        }).eq("id", row["opportunity_id"]).execute()


def get_trace(opportunity_id: str) -> dict[str, Any] | None:
    """Reassembles the reasoning trace for `/recommendation/{id}/trace`."""
    client = get_client()
    if client is None:
        row = _memory().get(opportunity_id)
        return row.get("trace") if row else None

    res = (
        client.table("reasoning_traces")
        .select("*")
        .eq("opportunity_id", opportunity_id)
        .order("created_at")
        .execute()
    )
    if not res.data:
        return None
    return {
        "opportunity_id": opportunity_id,
        "stages": [
            {
                "stage": r["stage"],
                "inputs_used": r["inputs_used"],
                "decision_rule_or_prompt_version": r["decision_rule_or_prompt_version"],
                "output_claim_ids": r["output_claim_ids"],
            }
            for r in res.data
        ],
    }


def list_inbound() -> list[dict[str, Any]]:
    """Inbound applications for the card grid (source=inbound)."""
    opps = list_opportunities()
    inbound = [o for o in opps if o.get("source") == "inbound"]
    inbound.sort(key=lambda o: (o.get("sla") or {}).get("signal_at") or "", reverse=True)
    return inbound


def get_company_profile(company_id: str, *, enrich: bool = True) -> dict[str, Any] | None:
    """Company profile + linked inbound/outbound opportunities."""
    from api.ingestion import company_enrich

    client = get_client()
    linked = [o for o in list_opportunities() if o.get("company_id") == company_id]
    if not linked and client is None:
        # Memory: match by company_id on full rows
        linked = [o for o in _memory().values() if o.get("company_id") == company_id]
        if not linked:
            return None
        primary = linked[0]
        enrichment = primary.get("company_enrichment") or {}
        if enrich and not enrichment.get("summary"):
            enrichment = company_enrich.enrich_company(primary["company_name"])
            primary["company_enrichment"] = enrichment
        return {
            "id": company_id,
            "name": primary.get("company_name"),
            "domain": primary.get("company_domain"),
            "sector": primary.get("company_sector"),
            "stage": primary.get("company_stage"),
            "description": enrichment.get("summary") or primary.get("company_description"),
            "enrichment": enrichment,
            "opportunities": linked,
            "primary_opportunity_id": primary.get("id"),
            "deck_url": primary.get("deck_url"),
            "has_deck": primary.get("has_deck"),
            "deck_filename": primary.get("deck_filename"),
        }

    if client is None:
        return None

    row = (
        client.table("companies")
        .select("id, name, domain, sector, stage, description, enrichment, enrichment_at")
        .eq("id", company_id)
        .limit(1)
        .execute()
    )
    if not row.data:
        return None
    company = row.data[0]
    name = company["name"]

    profile = company
    if enrich:
        profile = company_enrich.get_or_enrich_company(
            company_id,
            name,
            domain=company.get("domain"),
        )

    # Refresh linked after enrichment
    linked = [o for o in list_opportunities() if o.get("company_id") == company_id]
    primary = next((o for o in linked if o.get("source") == "inbound" and o.get("has_deck")), None)
    if primary is None and linked:
        primary = linked[0]

    return {
        "id": profile["id"],
        "name": profile["name"],
        "domain": profile.get("domain"),
        "sector": profile.get("sector"),
        "stage": profile.get("stage"),
        "description": profile.get("description"),
        "enrichment": profile.get("enrichment") or {},
        "opportunities": linked,
        "primary_opportunity_id": primary["id"] if primary else None,
        "deck_url": primary.get("deck_url") if primary else None,
        "has_deck": primary.get("has_deck") if primary else False,
        "deck_filename": primary.get("deck_filename") if primary else None,
    }
