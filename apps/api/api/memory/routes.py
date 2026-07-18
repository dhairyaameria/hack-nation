"""Memory layer REST surface, a thin adapter over `api.memory.store` (the
MCP server in `api.mcp.server` wraps the same functions for agents). See
docs/18-MEMORY-LAYER.md.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.core.db import get_client
from api.memory import store

router = APIRouter(tags=["memory"])


def _require_db() -> None:
    if get_client() is None:
        raise HTTPException(503, store.NO_SUPABASE_MSG)


class IngestRequest(BaseModel):
    title: str
    raw_text: str
    doc_type: str | None = None  # deck | memo | note | email
    founder_id: str | None = None
    company_id: str | None = None
    source_type: str = "note"
    source_locator: str | None = None
    source_timestamp: str | None = None


class SearchRequest(BaseModel):
    query: str
    founder_id: str | None = None
    company_id: str | None = None
    limit: int = 8


@router.post("/memory/ingest", status_code=201)
def ingest(payload: IngestRequest):
    _require_db()
    return store.ingest_document(**payload.model_dump())


@router.post("/memory/search")
def search(payload: SearchRequest):
    _require_db()
    results = store.search_memory(
        payload.query,
        founder_id=payload.founder_id,
        company_id=payload.company_id,
        limit=payload.limit,
    )
    return {"query": payload.query, "results": results}


@router.get("/memory/search")
def search_get(q: str, founder_id: str | None = None, company_id: str | None = None, limit: int = 8):
    _require_db()
    results = store.search_memory(q, founder_id=founder_id, company_id=company_id, limit=limit)
    return {"query": q, "results": results}


@router.get("/memory/facts")
def facts(
    fact_type: str | None = None,
    subject: str | None = None,
    as_of: str | None = None,
    include_invalidated: bool = False,
    limit: int = 50,
):
    _require_db()
    return {
        "facts": store.get_facts(
            fact_type=fact_type,
            subject=subject,
            as_of=as_of,
            include_invalidated=include_invalidated,
            limit=limit,
        )
    }
