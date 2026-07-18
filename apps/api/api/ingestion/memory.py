"""Bronze ingestion + entity resolution helpers (`docs/03-SOURCING.md` §2).

Every outbound connector writes through `ingest_raw` so every signal is
provenance-tagged (source, source_entity_id, fetched_at, run_id) before
anything downstream touches it. `resolve_founder` is deterministic for
Wave 2 (exact source-identity match, then case-insensitive name match,
then create) — an LLM fuzzy-match upgrade is a documented Wave 3 stretch.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from api.core.db import get_client

_MEMORY_BRONZE: list[dict[str, Any]] = []
_MEMORY_FOUNDERS: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest_raw(
    source: str,
    payload: dict[str, Any],
    *,
    entity_type: str | None = None,
    source_entity_id: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Writes one Bronze record. Never raises — a failed write degrades to
    an in-memory record rather than blocking the connector that called it.
    """
    row = {
        "id": str(uuid.uuid4()),
        "source": source,
        "source_entity_id": source_entity_id,
        "entity_type": entity_type,
        "payload": payload,
        "fetched_at": _now_iso(),
        "run_id": run_id,
    }
    client = get_client()
    if client is None:
        _MEMORY_BRONZE.append(row)
        return row
    try:
        return client.table("bronze_raw_events").insert(row).execute().data[0]
    except Exception as exc:  # noqa: BLE001 — ingestion must never crash the connector
        print(f"[memory] ingest_raw failed, keeping in-memory only: {exc}")
        _MEMORY_BRONZE.append(row)
        return row


def resolve_founder(
    display_name: str,
    *,
    source: str | None = None,
    source_entity_id: str | None = None,
) -> dict[str, Any]:
    """Deterministic identity resolution: exact (source, source_entity_id)
    match first, then case-insensitive display_name match, else create a
    new founder. Returns the founder row (dict with at least `id` and
    `display_name`).
    """
    client = get_client()
    if client is None:
        key = f"{source}:{source_entity_id}".lower() if source_entity_id else display_name.lower()
        existing = _MEMORY_FOUNDERS.get(key)
        if existing:
            return existing
        row = {"id": f"founder-{uuid.uuid4().hex[:8]}", "display_name": display_name, "source": source, "source_entity_id": source_entity_id}
        _MEMORY_FOUNDERS[key] = row
        _MEMORY_FOUNDERS[display_name.lower()] = row
        return row

    if source and source_entity_id:
        res = (
            client.table("founders")
            .select("*")
            .eq("source", source)
            .eq("source_entity_id", source_entity_id)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]

    res = client.table("founders").select("*").ilike("display_name", display_name).limit(1).execute()
    if res.data:
        return res.data[0]

    row = {
        "display_name": display_name,
        "domain_affinity": [],
        "source": source,
        "source_entity_id": source_entity_id,
        "fetched_at": _now_iso(),
    }
    return client.table("founders").insert(row).execute().data[0]


def resolve_company(name: str, *, domain: str | None = None, source: str | None = None) -> dict[str, Any]:
    client = get_client()
    if client is None:
        return {"id": f"company-{uuid.uuid4().hex[:8]}", "name": name, "domain": domain}

    if domain:
        res = client.table("companies").select("*").eq("domain", domain).limit(1).execute()
        if res.data:
            return res.data[0]

    res = client.table("companies").select("*").ilike("name", name).limit(1).execute()
    if res.data:
        return res.data[0]

    row = {"name": name, "domain": domain, "status": "active", "source": source, "fetched_at": _now_iso()}
    return client.table("companies").insert(row).execute().data[0]
