"""Persist and serve pitch deck PDFs for inbound preview cards.

Primary store is a local directory (works offline / without Storage setup).
When Supabase is configured, also mirrors the object into the `decks` bucket
so production deploys can share files across instances.
"""

from __future__ import annotations

import logging
from pathlib import Path

from api.core.db import get_client

logger = logging.getLogger(__name__)

# apps/api/var/decks — gitignored via var/
_ROOT = Path(__file__).resolve().parents[2] / "var" / "decks"
BUCKET = "decks"


def ensure_dir() -> Path:
    _ROOT.mkdir(parents=True, exist_ok=True)
    return _ROOT


def local_path(opportunity_id: str) -> Path:
    return ensure_dir() / f"{opportunity_id}.pdf"


def save_deck(opportunity_id: str, file_bytes: bytes, filename: str | None = None) -> dict[str, str]:
    """Write PDF to local disk; optionally mirror to Supabase Storage."""
    path = local_path(opportunity_id)
    path.write_bytes(file_bytes)
    storage_path = f"{opportunity_id}.pdf"
    safe_name = (filename or "deck.pdf").replace("/", "_")[:180]

    client = get_client()
    if client is not None:
        try:
            client.storage.from_(BUCKET).upload(
                storage_path,
                file_bytes,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )
        except Exception as exc:  # noqa: BLE001 — Storage optional at hackathon
            logger.warning("Supabase Storage upload skipped: %s", exc)

    return {
        "deck_filename": safe_name,
        "deck_storage_path": storage_path,
    }


def read_deck_bytes(opportunity_id: str, storage_path: str | None = None) -> bytes | None:
    path = local_path(opportunity_id)
    if path.is_file():
        return path.read_bytes()

    key = storage_path or f"{opportunity_id}.pdf"
    client = get_client()
    if client is None:
        return None
    try:
        return client.storage.from_(BUCKET).download(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Deck download failed for %s: %s", opportunity_id, exc)
        return None


def deck_api_path(opportunity_id: str) -> str:
    """Path the frontend prefixes with NEXT_PUBLIC_API_URL."""
    return f"/api/v1/inbound/applications/{opportunity_id}/deck"
