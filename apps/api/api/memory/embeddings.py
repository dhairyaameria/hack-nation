"""OpenAI embeddings wrapper for the memory layer.

Same degrade contract as `api.intelligence.llm`: no key configured, or any
API error, returns `None` so ingestion still stores documents/chunks (just
without vectors) and search falls back to keyword matching. The pipeline
never crashes because an embedding call failed (docs/00-OVERVIEW.md §4 rule 3).
"""

from __future__ import annotations

from api.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536  # matches vector(1536) in db/migrations/011_memory_layer.sql


def is_available() -> bool:
    return bool(settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    if not is_available() or not texts:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in resp.data]
    except Exception as exc:  # noqa: BLE001, any failure degrades to no-vector mode
        print(f"[memory.embeddings] OpenAI embeddings failed: {exc}")
        return None
