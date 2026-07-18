"""Fast first-pass screen — cheap heuristic before the expensive 3-axis
pipeline runs. See `docs/03-SOURCING.md` §1.

Wave 1: deterministic heuristic on claim count/content. Wave 2 swaps this
for a cheap LLM call without changing the `screen(...)` signature.
"""

from __future__ import annotations

MIN_CLAIMS_FOR_PASS = 2


def screen(company_name: str, claims: list[dict[str, str]]) -> tuple[str, str]:
    """Returns (verdict, reason). verdict is pass | reject | needs-more-info."""
    if not company_name.strip():
        return "reject", "No company name provided."
    if len(claims) == 0:
        return "needs-more-info", "No extractable claims found in the deck — ask for more detail."
    if len(claims) < MIN_CLAIMS_FOR_PASS:
        return "needs-more-info", "Deck has minimal substantive content — traction/product detail unclear."
    return "pass", f"Deck yielded {len(claims)} substantive claims — proceeding to 3-axis analysis."
