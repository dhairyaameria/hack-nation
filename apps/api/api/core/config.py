"""App-wide settings loaded from environment variables.

See `.env.example` at repo root for the full list. Falls back to
sensible dev defaults so the API boots even before Supabase/LLM keys
are configured (Gate G0 requirement).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

def _find_repo_root() -> Path:
    """Works in local monorepo and in Docker (`/app` + `/shared`)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "shared" / "fixtures").is_dir():
            return parent
        if (parent / ".env").is_file() and (parent / "apps").is_dir():
            return parent
    return here.parents[min(4, len(here.parents) - 1)]


REPO_ROOT = _find_repo_root()
load_dotenv(REPO_ROOT / ".env")
load_dotenv(Path.cwd() / ".env", override=False)

_shared = REPO_ROOT / "shared" / "fixtures"
FIXTURES_DIR = _shared if _shared.is_dir() else Path("/shared/fixtures")


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    web = os.getenv("NEXT_PUBLIC_WEB_URL", "").strip()
    if web and web not in origins:
        origins.append(web)
    # Local Next.js (hostname + port variants — browser Origin must match exactly)
    for o in (
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ):
        if o not in origins:
            origins.append(o)
    return origins


class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    perplexity_api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")

    cors_origins: list[str] = _cors_origins()
    # Preview + production Vercel deployments
    cors_origin_regex: str = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"https://.*\.vercel\.app",
    )

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)


settings = Settings()
