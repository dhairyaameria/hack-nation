"""App-wide settings loaded from environment variables.

See `.env.example` at repo root for the full list. Falls back to
sensible dev defaults so the API boots even before Supabase/LLM keys
are configured (Gate G0 requirement).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load root .env (repo root, four levels up from apps/api/api/core/)
REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPO_ROOT / ".env")

FIXTURES_DIR = REPO_ROOT / "shared" / "fixtures"


class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    perplexity_api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    cors_origins: list[str] = [
        os.getenv("NEXT_PUBLIC_WEB_URL", "http://localhost:3000"),
    ]

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)


settings = Settings()
