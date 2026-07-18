"""GitHub connector (`docs/03-SOURCING.md` §2.1) — repo growth, commit
consistency (proxied by recent push activity), and follower reach.
Public REST API, no auth required, cached in Bronze via `ingest_raw`.

A 404 (no such user) or any network failure returns `None` — this is a
core cold-start signal: absence of a GitHub footprint must never be
scored as a negative, only as "no signal from this channel"
(`docs/00-OVERVIEW.md` §4 rule 3/6).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from api.ingestion.memory import ingest_raw

GITHUB_API = "https://api.github.com"


def fetch_profile_signals(username: str) -> dict[str, Any] | None:
    try:
        with httpx.Client(timeout=10, headers={"Accept": "application/vnd.github+json"}) as http:
            profile_resp = http.get(f"{GITHUB_API}/users/{username}")
            if profile_resp.status_code == 404:
                return None
            profile_resp.raise_for_status()
            profile = profile_resp.json()

            repos_resp = http.get(f"{GITHUB_API}/users/{username}/repos", params={"sort": "pushed", "per_page": 20})
            repos_resp.raise_for_status()
            repos = repos_resp.json()
    except Exception as exc:  # noqa: BLE001 — connector failures degrade to "no signal", never crash
        print(f"[github] fetch failed for {username!r}: {exc}")
        return None

    own_repos = [r for r in repos if not r.get("fork")]
    total_stars = sum(r.get("stargazers_count", 0) for r in own_repos)
    now = datetime.now(timezone.utc)
    recently_pushed = [
        r for r in own_repos
        if r.get("pushed_at") and (now - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days <= 90
    ]
    account_age_years = None
    if profile.get("created_at"):
        created = datetime.fromisoformat(profile["created_at"].replace("Z", "+00:00"))
        account_age_years = round((now - created).days / 365.25, 1)

    signals = {
        "username": username,
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "own_repo_count": len(own_repos),
        "total_stars": total_stars,
        "repos_pushed_last_90d": len(recently_pushed),
        "account_age_years": account_age_years,
        "bio": profile.get("bio"),
        "most_recent_push": own_repos[0].get("pushed_at") if own_repos else None,
        "profile_url": profile.get("html_url"),
    }

    ingest_raw("github", signals, entity_type="founder_profile", source_entity_id=username)
    return signals
