"""Memory layer data access, backed by `documents`, `document_chunks`,
`memory_facts`, `actor_aliases` (migration 009). This is the ONE place that
touches those tables: REST routes (`api.memory.routes`), MCP tools
(`api.mcp.server`), and scheduled pipelines (`jobs/pipelines/`) are all thin
adapters over these functions. See docs/18-MEMORY-LAYER.md.

Unlike the fixture-backed stores, the memory layer has no in-memory
fallback: every function raises RuntimeError when Supabase is not
configured (callers surface it as HTTP 503 / a tool error).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.core.db import get_client
from api.memory import embeddings, extraction

CHUNK_CHAR_TARGET = 1000
NO_SUPABASE_MSG = "Memory layer requires Supabase credentials in .env (see .env.example)."


def _client():
    client = get_client()
    if client is None:
        raise RuntimeError(NO_SUPABASE_MSG)
    return client


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunk_text(text: str) -> list[str]:
    """Greedy paragraph packing into ~CHUNK_CHAR_TARGET-char chunks."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        if current and len(current) + len(p) > CHUNK_CHAR_TARGET:
            chunks.append(current)
            current = p
        else:
            current = f"{current}\n\n{p}" if current else p
    if current:
        chunks.append(current)
    return chunks or ([text.strip()] if text.strip() else [])


def _provenance_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": row["source_type"],
        "source_locator": row["source_locator"],
        "source_timestamp": row.get("source_timestamp"),
    }


def _chunk_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "document_id": row["document_id"],
        "chunk_index": row["chunk_index"],
        "content": row["content"],
        "founder_id": row.get("founder_id"),
        "company_id": row.get("company_id"),
        "provenance": _provenance_out(row),
        "similarity": row.get("similarity"),
    }


def _fact_out(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "fact_type": row["fact_type"],
        "subject": row["subject"],
        "body": row["body"],
        "payload": row.get("payload") or {},
        "founder_id": row.get("founder_id"),
        "company_id": row.get("company_id"),
        "document_id": row.get("document_id"),
        "confidence": row.get("confidence"),
        "valid_from": row.get("valid_from"),
        "valid_until": row.get("valid_until"),
        "provenance": _provenance_out(row),
    }


def ingest_document(
    *,
    title: str,
    raw_text: str,
    doc_type: str | None = None,
    founder_id: str | None = None,
    company_id: str | None = None,
    source_type: str = "note",
    source_locator: str | None = None,
    source_timestamp: str | None = None,
) -> dict[str, Any]:
    """Stores the document, chunks + embeds the text, and runs one LLM pass
    to extract structured facts. Everything lands with provenance. Embedding
    and extraction degrade to no-ops when OPENAI_API_KEY is missing.
    """
    client = _client()
    locator = source_locator or title

    doc = client.table("documents").insert({
        "title": title,
        "doc_type": doc_type,
        "raw_text": raw_text,
        "founder_id": founder_id,
        "company_id": company_id,
        "source_type": source_type,
        "source_locator": locator,
        "source_timestamp": source_timestamp,
    }).execute().data[0]

    chunks = chunk_text(raw_text)
    vectors = embeddings.embed_texts(chunks)
    chunk_rows = [
        {
            "document_id": doc["id"],
            "chunk_index": i,
            "content": content,
            "embedding": vectors[i] if vectors else None,
            "founder_id": founder_id,
            "company_id": company_id,
            "source_type": source_type,
            "source_locator": f"{locator}#chunk-{i}",
            "source_timestamp": source_timestamp,
        }
        for i, content in enumerate(chunks)
    ]
    if chunk_rows:
        client.table("document_chunks").upsert(chunk_rows, on_conflict="document_id,chunk_index").execute()

    facts = extraction.extract_facts(raw_text, subject_hint=title)
    fact_rows = [
        {
            **f,
            "founder_id": founder_id,
            "company_id": company_id,
            "document_id": doc["id"],
            "source_type": source_type,
            "source_locator": locator,
            "source_timestamp": source_timestamp,
        }
        for f in facts
    ]
    if fact_rows:
        client.table("memory_facts").insert(fact_rows).execute()

    return {
        "document_id": doc["id"],
        "title": title,
        "chunks_stored": len(chunk_rows),
        "embedded": vectors is not None,
        "facts_extracted": len(fact_rows),
    }


def search_memory(
    query: str,
    *,
    founder_id: str | None = None,
    company_id: str | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Semantic search over document chunks (cosine, via the
    `match_document_chunks` SQL function from migration 009). Falls back to
    keyword matching when no embedding key is configured.
    """
    client = _client()

    vectors = embeddings.embed_texts([query])
    if vectors is not None:
        res = client.rpc("match_document_chunks", {
            "query_embedding": vectors[0],
            "match_count": limit,
            "filter_founder_id": founder_id,
            "filter_company_id": company_id,
        }).execute()
        return [_chunk_out(row) for row in (res.data or [])]

    q = client.table("document_chunks").select("*").ilike("content", f"%{query}%")
    if founder_id:
        q = q.eq("founder_id", founder_id)
    if company_id:
        q = q.eq("company_id", company_id)
    res = q.limit(limit).execute()
    return [_chunk_out(row) for row in (res.data or [])]


def get_facts(
    *,
    fact_type: str | None = None,
    subject: str | None = None,
    as_of: str | None = None,
    include_invalidated: bool = False,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Filter facts by type/subject. `as_of` returns what was believed true at
    that moment (valid_from <= as_of < valid_until). Default: current facts only.
    """
    client = _client()
    q = client.table("memory_facts").select("*")
    if fact_type:
        q = q.eq("fact_type", fact_type)
    if subject:
        q = q.ilike("subject", f"%{subject}%")
    if as_of:
        q = q.lte("valid_from", as_of).or_(f"valid_until.is.null,valid_until.gt.{as_of}")
    elif not include_invalidated:
        q = q.is_("valid_until", "null")
    res = q.order("valid_from", desc=True).limit(limit).execute()
    return [_fact_out(row) for row in (res.data or [])]


def invalidate_fact(fact_id: str, valid_until: str | None = None) -> dict[str, Any] | None:
    """Bi-temporal-lite: mark a fact as no longer true instead of deleting it."""
    client = _client()
    res = (
        client.table("memory_facts")
        .update({"valid_until": valid_until or _now_iso()})
        .eq("id", fact_id)
        .execute()
    )
    return _fact_out(res.data[0]) if res.data else None


def resolve_actor(
    alias: str,
    alias_type: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any] | None:
    """Maps an email/handle/name to one canonical founder via `actor_aliases`.
    Unknown alias + a display_name creates the founder and registers the
    alias. Unknown alias without a display_name returns None.
    """
    client = _client()
    alias_type = alias_type or ("email" if "@" in alias else "name")

    res = (
        client.table("actor_aliases")
        .select("founder_id, alias, alias_type")
        .eq("alias_type", alias_type)
        .ilike("alias", alias)
        .limit(1)
        .execute()
    )
    if res.data:
        return {"founder_id": res.data[0]["founder_id"], "alias": alias, "created": False}

    if display_name is None:
        return None

    founder = client.table("founders").insert({"display_name": display_name, "domain_affinity": []}).execute().data[0]
    client.table("actor_aliases").insert({
        "founder_id": founder["id"],
        "alias": alias,
        "alias_type": alias_type,
    }).execute()
    return {"founder_id": founder["id"], "alias": alias, "created": True}
