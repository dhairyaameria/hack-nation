"""Shared Supabase client. Single source of truth for DB access — every
`*_store.py` module imports `get_client()` instead of constructing its own
client, so there is exactly one place that knows about credentials.
"""

from __future__ import annotations

from functools import lru_cache

from api.core.config import settings


@lru_cache(maxsize=1)
def get_client():
    """Returns a Supabase client, or None if credentials aren't configured
    (callers fall back to fixtures/in-memory data — see `docs/16-MIGRATIONS-GUIDE.md`).
    """
    if not settings.has_supabase:
        return None
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_key)
