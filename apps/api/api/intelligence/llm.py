"""OpenAI wrapper for the Analyst/Validator/Referee pipeline.

Every call degrades gracefully: no key configured, or any API error,
returns `None` so callers fall back to the Wave 1 heuristic — the pipeline
never crashes or fabricates data because an LLM call failed (see
`docs/00-OVERVIEW.md` §4 rule 3).
"""

from __future__ import annotations

import json

from api.core.config import settings

MODEL = "gpt-4o-mini"


def is_available() -> bool:
    return bool(settings.openai_api_key)


def chat_json(system: str, user: str) -> dict | None:
    if not is_available():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as exc:  # noqa: BLE001 — any failure here must degrade, not crash the pipeline
        print(f"[llm] OpenAI call failed, falling back to heuristic: {exc}")
        return None
