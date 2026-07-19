"""Boundary-aware text clipping — never cut mid-word / mid-citation / mid-bullet."""

from __future__ import annotations

import re

_EMPTY_BULLET = re.compile(r"^\s*([-*•]|\d+[.)])\s*$")
_OPEN_CITATION = re.compile(r"\[\d*$")
_MD_HEADING = re.compile(r"#{1,6}\s+")
_MD_EMPHASIS = re.compile(r"(\*\*|__|\*|_|~~|`)")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_MD_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
_MD_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$", re.MULTILINE)
_MD_LIST = re.compile(r"^\s*([-*•]|\d+[.)])\s+", re.MULTILINE)
_WS = re.compile(r"\s+")


def plain_snippet(text: str, max_len: int = 320) -> str:
    """Turn scraped page / markdown blobs into a short prose citation excerpt.

    Search APIs often return raw markdown (``# Heading``, tables, etc.). Showing
    that as plain text looks like "random markdown frags" — strip structure first,
    then boundary-clip.
    """
    return clip_text(_strip_markdown_noise(text), max_len)


def _strip_markdown_noise(text: str) -> str:
    s = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    s = _MD_IMAGE.sub("", s)
    s = _MD_LINK.sub(r"\1", s)
    s = _MD_TABLE_SEP.sub(" ", s)
    s = _MD_TABLE_ROW.sub(lambda m: " " + m.group(0).replace("|", " ") + " ", s)
    s = _MD_HEADING.sub(" ", s)
    s = _MD_LIST.sub("", s)
    s = _MD_EMPHASIS.sub("", s)
    s = s.replace("|", " ")
    # Repair "word.Next" joins left when a heading sat between sentences.
    s = re.sub(r"([.!?])([A-Z])", r"\1 \2", s)
    return _WS.sub(" ", s).strip()


def _tidy_incomplete_tail(chunk: str) -> str:
    """Drop dangling list markers / open emphasis / partial [N] citations."""
    lines = chunk.splitlines()
    while lines and _EMPTY_BULLET.match(lines[-1]):
        lines.pop()
    chunk = "\n".join(lines).rstrip()

    # Unclosed **bold** from a mid-span cut — drop the trailing open marker + remnant.
    if chunk.count("**") % 2 == 1:
        last = chunk.rfind("**")
        if last != -1:
            chunk = chunk[:last].rstrip()

    # Partial citation like "[1" or "[" at the end.
    chunk = _OPEN_CITATION.sub("", chunk).rstrip()

    # If we still end on an empty bullet after the above, strip again.
    lines = chunk.splitlines()
    while lines and _EMPTY_BULLET.match(lines[-1]):
        lines.pop()
    return "\n".join(lines).rstrip()


def clip_text(text: str, max_len: int, *, ellipsis: bool = True) -> str:
    """Truncate at a paragraph / sentence / word boundary when possible.

    Hard ``s[:N]`` slices produce the mid-token artifacts we show in the UI
    (e.g. ``$3 billio``, empty trailing bullets, half-open ``**``). Prefer this.
    """
    text = (text or "").strip()
    if max_len <= 0 or len(text) <= max_len:
        return text

    budget = max(1, max_len - (1 if ellipsis else 0))
    chunk = text[:budget]

    cut: int | None = None
    for sep in ("\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "):
        idx = chunk.rfind(sep)
        # Don't collapse the whole string — only accept late boundaries.
        if idx >= max(budget // 2, min(40, budget // 3)):
            if sep in (". ", "! ", "? "):
                cut = idx + 1  # keep the terminator
            else:
                cut = idx
            break
    if cut is not None:
        chunk = chunk[:cut]

    chunk = _tidy_incomplete_tail(chunk)
    if ellipsis and chunk and not chunk.endswith(("…", ".", "!", "?", ":", ";")):
        chunk += "…"
    return chunk
