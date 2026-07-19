"""MCP server for the VC Brain memory layer. Agents connect here; the
dashboard uses REST (`api.memory.routes`). Both are thin adapters over the
same service functions, so there is no duplicated logic to drift. See
docs/18-MEMORY-LAYER.md.

Run (stdio transport, for Cursor/Claude MCP configs):

    make mcp
    # or: cd apps/api && source .venv/bin/activate && python -m api.mcp.server
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from api.core import founder_store
from api.ingestion import fast_screen
from api.memory import store

mcp = FastMCP("vc-brain")


@mcp.tool
def search_memory(
    query: str,
    founder_id: str | None = None,
    company_id: str | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Semantic search over everything ingested into the company brain
    (decks, memos, notes, emails). Returns text chunks with provenance
    (source_type, source_locator, source_timestamp) and similarity scores.
    Optionally filter to one founder_id or company_id (UUIDs).
    """
    return store.search_memory(query, founder_id=founder_id, company_id=company_id, limit=limit)


@mcp.tool
def get_facts(
    fact_type: str | None = None,
    subject: str | None = None,
    as_of: str | None = None,
    include_invalidated: bool = False,
) -> list[dict[str, Any]]:
    """Query structured facts extracted at ingestion time. fact_type is one
    of actor | decision | commitment | claim. subject matches the person or
    company the fact is about. as_of (ISO timestamp) returns what was
    believed true at that moment; by default only currently-valid facts
    (valid_until is null) are returned.
    """
    return store.get_facts(
        fact_type=fact_type,
        subject=subject,
        as_of=as_of,
        include_invalidated=include_invalidated,
    )


@mcp.tool
def get_founder_profile(founder_id: str) -> dict[str, Any] | None:
    """Founder Genome profile for one founder (UUID): score history, genome
    dimensions, domain affinity, and network proximity with disclosure.
    """
    return founder_store.get_founder_profile(founder_id)


@mcp.tool
def screen_opportunity(company_name: str, claims: list[str]) -> dict[str, str]:
    """Fast first-pass screen on an opportunity given its company name and
    a list of claim texts (e.g. from a deck). Returns a verdict of
    pass | reject | needs-more-info plus a one-line reason.
    """
    verdict, reason = fast_screen.screen(company_name, [{"text": c} for c in claims])
    return {"verdict": verdict, "reason": reason}


if __name__ == "__main__":
    mcp.run()
