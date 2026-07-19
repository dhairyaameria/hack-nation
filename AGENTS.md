# AGENTS.md

Instructions for AI coding agents. Read before making changes.

## Project overview

VC Brain: a one-day hackathon build of a data- and AI-first venture operating
system that discovers founders, runs diligence, and produces $100K investment
recommendations. Two areas share ONE Supabase Postgres + pgvector database:

- **Product 1 (main): unified memory layer ("company brain").** Ingests
  unstructured content (decks, memos, notes, emails) plus structured entities.
  Agents query it via MCP tools, the dashboard via REST. Both are thin
  adapters over the same service functions in `apps/api/api/memory/store.py`.
- **Product 2: scheduled specialist agent pipelines** for inbound/outbound
  deal flow (sourcing, 3-axis screening, diligence, memo + trust, decision).
  Lives in `jobs/pipelines/`, reads/writes the same memory.

Current status: Waves 1-2 landed (deck parsing, fast screen, real
Analyst/Validator/Referee scoring wired to OpenAI + Tavily, live Supabase).
Memory layer + MCP server + pipeline skeleton scaffolded (migration 012,
`api/memory/`, `api/mcp/`, `jobs/pipelines/`).

Binding product rules live in `docs/00-OVERVIEW.md` §4. Key ones: never
average the 3 axes into one score, never fabricate data when an API call
fails (degrade to heuristics/unknown), per-claim trust with provenance.

## Tech stack

- **API:** FastAPI (Python 3.11), Supabase Python client, OpenAI
  (gpt-4o-mini + text-embedding-3-small), Tavily search, FastMCP.
- **DB:** Supabase Postgres + pgvector. Plain SQL migrations in
  `db/migrations/`, applied manually in order (no migration framework).
- **Web:** Next.js dashboard in `apps/web` (fixture-driven fallbacks).
- **Contracts:** Pydantic models in `shared/schemas/models.py`, mirrored by
  hand in `shared/schemas/types.ts`.

## Repository layout

```
apps/api/
  main.py               FastAPI entrypoint (route registration only)
  api/core/             config, Supabase client, fixtures, founder/opportunity stores
  api/ingestion/        Agent B: deck parsing, fast screen, inbound routes
  api/intelligence/     Agent C: Analyst/Validator/Referee, llm.py, retrieval.py
  api/agent/            Agent D: thesis CRUD, agent chat stub
  api/memory/           memory layer: store.py (single data-access path),
                        embeddings.py, extraction.py, routes.py
  api/mcp/server.py     FastMCP stdio server (agents' entry point)
apps/web/               Next.js dashboard (do not touch from API tasks)
db/migrations/          001-009 ordered SQL (009 = memory layer)
db/seed/seed.py         idempotent demo seed (uuid5 slugs), incl. memory data
jobs/pipelines/         Product 2 scheduled runs (daily_pipeline.py)
shared/schemas/         models.py + types.ts (keep in sync)
shared/fixtures/        offline demo JSON used when Supabase is not configured
docs/                   00-18 specs; 17 = module ownership, 18 = memory layer
```

## Development commands

```bash
# one-time: venv lives at apps/api/.venv
cd apps/api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

make dev-api    # uvicorn on :8000 (falls back to fixtures without .env)
make dev-web    # Next.js on :3000
make db-reset   # apply db/migrations/*.sql via psql ($DATABASE_URL)
make db-seed    # python db/seed/seed.py (needs Supabase creds in .env)
make mcp        # FastMCP stdio server (api.mcp.server)
make pipeline   # Product 2 daily loop (jobs/pipelines/daily_pipeline.py)
```

Copy `.env.example` to `.env` for Supabase/OpenAI/Tavily keys. Everything
degrades gracefully without them (fixtures, heuristics, keyword search).

## Where to work

| Task | Start here |
|------|-----------|
| Ingest/search/facts (memory layer) | `apps/api/api/memory/store.py` + `docs/18-MEMORY-LAYER.md` |
| New MCP tool for agents | `apps/api/api/mcp/server.py` (wrap an existing function, keep it thin) |
| Schema change | `db/migrations/` (Agent A owns, see `docs/17-PARALLEL-WORKFLOW.md`) |
| Scoring / trust / memos | `apps/api/api/intelligence/` |
| Inbound applications / screening | `apps/api/api/ingestion/` |
| Thesis / agent chat | `apps/api/api/agent/` |
| Scheduled pipeline runs | `jobs/pipelines/daily_pipeline.py` |
| Shared shapes | `shared/schemas/models.py` and `types.ts` (same commit) |
| Demo data | `db/seed/seed.py` + `docs/14-SEED-DATA-SPEC.md` |
| Dashboard UI | `apps/web` (Agent E; keep fixture IDs aligned with seed) |

Respect module ownership in `docs/17-PARALLEL-WORKFLOW.md`: additive changes
only, no renames of existing routes/contracts, match the existing code style
(degrade-not-crash wrappers, store modules over ORMs, small plain functions).

## Maintaining this file

Update this file in the same commit when structure, architecture, dev
commands, or milestones change. Keep it ~100-150 lines, surgical edits only.
