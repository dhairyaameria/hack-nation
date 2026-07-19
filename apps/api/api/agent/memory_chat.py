"""Chief-of-staff answers for VC Agent Chat, grounded in the unified memory
layer (`api.memory.store`). Retrieves note/deck chunks plus structured facts
(commitments, decisions, claims), then composes a reply that may only use
that retrieved context. Every answer carries citations from provenance.
Degrades honestly: no Supabase means "memory unavailable", and no OpenAI key
means a verbatim extract instead of a composed summary, never a made-up one.
"""

from __future__ import annotations

from typing import Any

from api.intelligence import llm
from api.memory import store as memory_store

_MAX_CHUNKS = 5
_MAX_FACTS = 30


def _citation(provenance: dict[str, Any], snippet: str) -> dict[str, Any]:
    return {
        "source_type": provenance.get("source_type"),
        "source_locator": provenance.get("source_locator"),
        "snippet": snippet[:200],
    }


def _compose_llm(question: str, chunks: list[dict], facts: list[dict]) -> str | None:
    system = (
        "You are the chief of staff for a VC fund. Answer the partner's question using ONLY "
        "the memory excerpts and structured facts provided. Facts may include commitments "
        "(promises with due dates), decisions, and claims; a fact with a valid_until timestamp "
        "was superseded later, so prefer the current fact and you may note what changed. "
        "If the context does not contain the answer, say the memory has nothing on it. "
        "Be concise (2-5 sentences) and mention source names when useful. "
        'Return strict JSON: {"answer": "..."}'
    )
    fact_lines = [
        f"- [{f['fact_type']}] {f['body']}"
        + (f" (superseded {f['valid_until'][:10]})" if f.get("valid_until") else "")
        for f in facts
    ]
    chunk_lines = [f"- ({c['provenance'].get('source_locator')}) {c['content']}" for c in chunks]
    user = (
        f"Question: {question}\n\nMemory excerpts:\n" + ("\n".join(chunk_lines) or "(none)")
        + "\n\nFacts:\n" + ("\n".join(fact_lines) or "(none)")
    )
    data = llm.chat_json(system, user)
    if data and isinstance(data.get("answer"), str) and data["answer"].strip():
        return data["answer"].strip()
    return None


def _compose_fallback(chunks: list[dict], facts: list[dict]) -> str:
    if not chunks and not facts:
        return "Memory has nothing matching that question yet."
    parts = ["From memory (no LLM available, showing raw excerpts):"]
    for c in chunks[:2]:
        parts.append(f"• {c['content'][:280]}")
    for f in facts[:4]:
        parts.append(f"• [{f['fact_type']}] {f['body']}")
    return "\n".join(parts)


def answer(question: str) -> dict[str, Any]:
    """Returns {reply, citations, available}. `available=False` means the
    memory layer itself was unreachable (no Supabase configured)."""
    try:
        chunks = memory_store.search_memory(question, limit=_MAX_CHUNKS)
        # Current facts only (valid_until is null): what we believe true now.
        facts = memory_store.get_facts(limit=_MAX_FACTS)
    except RuntimeError as exc:
        return {"reply": str(exc), "citations": [], "available": False}
    except Exception as exc:  # noqa: BLE001 — degrade, never crash the chat turn
        return {"reply": f"Memory lookup failed: {exc}", "citations": [], "available": False}

    reply = _compose_llm(question, chunks, facts) if llm.is_available() else None
    if reply is None:
        reply = _compose_fallback(chunks, facts)

    citations = [_citation(c["provenance"], c["content"]) for c in chunks]
    citations += [_citation(f["provenance"], f["body"]) for f in facts[:5]]
    seen: set[str] = set()
    deduped = []
    for c in citations:
        key = c.get("source_locator") or ""
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return {"reply": reply, "citations": deduped, "available": True}
