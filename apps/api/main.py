"""FastAPI entrypoint. Route registration only — see
`docs/17-PARALLEL-WORKFLOW.md` for module ownership (agents own their
own routers under `api/<module>/routes.py`; this file just wires them up).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agent.routes import router as agent_router
from api.core.config import settings
from api.ingestion.routes import router as ingestion_router
from api.intelligence.routes import router as intelligence_router

app = FastAPI(title="VC Brain API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(ingestion_router, prefix=API_PREFIX)
app.include_router(intelligence_router, prefix=API_PREFIX)
app.include_router(agent_router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"service": "vc-brain-api", "status": "ok"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "supabase_connected": settings.has_supabase,
    }
