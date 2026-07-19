"""Perplexity Sonar client — search-grounded chat completions.

Used by inbound rerank (`api.ingestion.inbound_rerank`). Degrades to None
on missing key or API failure so callers never fabricate rankings.
"""

from __future__ import annotations

import json
import re

import httpx

from api.core.config import settings

# OpenAI-compatible Chat Completions endpoint (widely supported).
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar"


def is_available() -> bool:
    return bool(settings.perplexity_api_key)


def chat(system: str, user: str, *, temperature: float = 0.2) -> dict | None:
    """Returns `{content, citations}` or None on any failure."""
    if not is_available():
        return None
    try:
        resp = httpx.post(
            PERPLEXITY_URL,
            headers={
                "Authorization": f"Bearer {settings.perplexity_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
            },
            timeout=90.0,
        )
        resp.raise_for_status()
        payload = resp.json()
        content = payload["choices"][0]["message"]["content"]
        citations = payload.get("citations") or []
        return {"content": content, "citations": citations}
    except Exception as exc:  # noqa: BLE001 — degrade, never crash callers
        print(f"[perplexity] call failed: {exc}")
        return None


def chat_json(system: str, user: str) -> dict | None:
    """Like chat(), but parses a JSON object from the assistant content."""
    result = chat(system, user)
    if result is None:
        return None
    parsed = _extract_json(result["content"])
    if parsed is None:
        print("[perplexity] could not parse JSON from response")
        return None
    parsed["_citations"] = result.get("citations") or []
    return parsed


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            return None
    return None
