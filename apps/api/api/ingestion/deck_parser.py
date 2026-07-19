"""Deck parsing — extract text from an uploaded PDF and split it into
claims with page-number locators.

Wave 1: heuristic extraction only (no LLM call — no OPENAI_API_KEY needed
to demo the inbound flow). Wave 2 swaps `_split_into_claims` for an OpenAI
structured-output call per `docs/03-SOURCING.md` §1 without changing the
function signature `parse_deck(...)` that `routes.py` calls.
"""

from __future__ import annotations

import re

from pypdf import PdfReader

TRACTION_KEYWORDS = re.compile(
    r"\$|%|ARR|MRR|customers?|users?|revenue|growth|partners?|pilot|waitlist|LOI",
    re.IGNORECASE,
)


def extract_deck_text(file_bytes: bytes, *, max_chars: int = 12000) -> str:
    """Full-text extract from a PDF for rerank / research prompts.

    Truncates to `max_chars` so Perplexity prompts stay bounded. Never raises.
    """
    try:
        import io

        reader = PdfReader(io.BytesIO(file_bytes))
        parts: list[str] = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                parts.append(f"[slide {page_num}]\n{text}")
        joined = "\n\n".join(parts)
        if len(joined) > max_chars:
            return joined[:max_chars] + "\n…[truncated]"
        return joined
    except Exception:
        return ""


def parse_deck(file_bytes: bytes) -> list[dict[str, str]]:
    """Returns a list of `{text, slide_locator}` claims extracted from a PDF.

    Falls back to an empty list (never raises) so a malformed upload
    degrades gracefully instead of crashing the submission flow — see
    `docs/17-PARALLEL-WORKFLOW.md` §9 external API / robustness discipline.
    """
    claims: list[dict[str, str]] = []
    try:
        import io

        reader = PdfReader(io.BytesIO(file_bytes))
        for page_num, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            for sentence in _split_into_claims(text):
                claims.append({"text": sentence, "slide_locator": f"slide {page_num}"})
    except Exception:
        return []
    return claims


def _split_into_claims(text: str) -> list[str]:
    """Heuristic: prioritize sentences that look like traction/metric claims,
    then fall back to any substantive line. Real LLM extraction (team,
    problem, product, traction, market, ask categories) lands in Wave 2.
    """
    lines = [ln.strip() for ln in re.split(r"[\n.]", text) if len(ln.strip()) > 12]
    scored = sorted(lines, key=lambda ln: bool(TRACTION_KEYWORDS.search(ln)), reverse=True)
    return scored[:5]
