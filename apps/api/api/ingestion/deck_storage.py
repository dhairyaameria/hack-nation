"""Upload / download pitch decks from the Supabase `decks` storage bucket.

Paths are stored on `opportunities.deck_storage_path` + `deck_url` so rerank
(and later the UI) can fetch the same artifact the founder uploaded.
"""

from __future__ import annotations

import re
from typing import Any

from api.core.db import get_client

BUCKET = "decks"
_bucket_ready = False


def _safe_filename(name: str | None) -> str:
    base = (name or "deck.pdf").strip() or "deck.pdf"
    base = re.sub(r"[^\w.\-]+", "_", base)
    if not base.lower().endswith(".pdf"):
        base = f"{base}.pdf"
    return base[:180]


def _ensure_bucket(client) -> None:
    """Create the public `decks` bucket once if it does not exist yet."""
    global _bucket_ready
    if _bucket_ready:
        return
    try:
        buckets = client.storage.list_buckets()
        names = {
            getattr(b, "name", None) or (b.get("name") if isinstance(b, dict) else None)
            for b in (buckets or [])
        }
        if BUCKET not in names:
            try:
                client.storage.create_bucket(BUCKET, options={"public": True})
            except TypeError:
                client.storage.create_bucket(BUCKET, public=True)
            print(f"[deck_storage] created bucket {BUCKET!r}")
        _bucket_ready = True
    except Exception as exc:  # noqa: BLE001
        print(f"[deck_storage] ensure_bucket failed: {exc}")


def upload_deck(opportunity_id: str, file_bytes: bytes, filename: str | None) -> dict[str, str]:
    """Uploads bytes to Storage. Returns `{deck_storage_path, deck_url, deck_filename}`.

    If Supabase/Storage is unavailable, still returns a synthetic path so the
    DB row can record that a deck was submitted (URL may be empty).
    """
    safe = _safe_filename(filename)
    path = f"{opportunity_id}/{safe}"
    client = get_client()
    if client is None:
        return {"deck_storage_path": path, "deck_url": "", "deck_filename": safe}

    _ensure_bucket(client)
    try:
        client.storage.from_(BUCKET).upload(
            path,
            file_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )
        url = client.storage.from_(BUCKET).get_public_url(path)
    except Exception as exc:  # noqa: BLE001
        print(f"[deck_storage] upload failed for {path}: {exc}")
        url = ""

    return {"deck_storage_path": path, "deck_url": url or "", "deck_filename": safe}


def download_deck(storage_path: str) -> bytes | None:
    """Fetches deck bytes from Storage, or None if unavailable."""
    if not storage_path:
        return None
    client = get_client()
    if client is None:
        return None
    try:
        return client.storage.from_(BUCKET).download(storage_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[deck_storage] download failed for {storage_path}: {exc}")
        return None


def attach_deck_fields(opp: dict[str, Any], deck_meta: dict[str, str]) -> dict[str, Any]:
    return {**opp, **deck_meta}
