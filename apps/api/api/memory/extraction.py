"""Write-time fact extraction (Sentra-inspired): one LLM call per ingested
document pulls structured facts (actors, decisions, commitments, claims) so
agents can later query meaning instead of re-reading raw text. See
docs/18-MEMORY-LAYER.md.

Reuses `api.intelligence.llm.chat_json`, which already degrades gracefully:
no key or a malformed response returns an empty list and ingestion still
stores the document + chunks.
"""

from __future__ import annotations

from api.intelligence import llm

VALID_FACT_TYPES = {"actor", "decision", "commitment", "claim"}
MAX_DOC_CHARS = 8000  # keep the extraction call cheap on long documents


def extract_facts(raw_text: str, subject_hint: str | None = None) -> list[dict]:
    """Returns a list of {fact_type, subject, body, payload, confidence} dicts."""
    if not llm.is_available():
        return []
    system = (
        "You extract structured facts from an unstructured VC document (deck notes, "
        "call notes, memo, email) so an investment team's memory layer can answer "
        "questions later without re-reading the text. Extract only what the text "
        "supports. NEVER invent facts.\n\n"
        "Fact types:\n"
        "- actor: a person/org and their role (e.g. 'Alex Rivera is CEO of Rivera Labs')\n"
        "- decision: a decision that was made ('we passed on X', 'moving to diligence')\n"
        "- commitment: someone promised to do something, ideally with a deadline\n"
        "- claim: a factual assertion worth verifying (ARR, customers, team size)\n\n"
        "Return strict JSON:\n"
        '{"facts": [{"fact_type": "actor|decision|commitment|claim", '
        '"subject": <who/what the fact is about>, '
        '"body": <one plain-English sentence>, '
        '"payload": <object with structured detail: amounts, dates, parties>, '
        '"confidence": <0.0-1.0>}]}'
    )
    user = (f"Document subject hint: {subject_hint}\n\n" if subject_hint else "") + raw_text[:MAX_DOC_CHARS]
    data = llm.chat_json(system, user)
    if not data:
        return []

    out = []
    for f in data.get("facts", []):
        if not isinstance(f, dict) or f.get("fact_type") not in VALID_FACT_TYPES:
            continue
        if not f.get("subject") or not f.get("body"):
            continue
        try:
            confidence = round(max(0.0, min(1.0, float(f.get("confidence", 0.5)))), 2)
        except (TypeError, ValueError):
            confidence = 0.5
        out.append({
            "fact_type": f["fact_type"],
            "subject": str(f["subject"]),
            "body": str(f["body"]),
            "payload": f.get("payload") if isinstance(f.get("payload"), dict) else {},
            "confidence": confidence,
        })
    return out
