# 18 - Memory Layer + MCP Surface

**Owner:** team-k (memory/MCP scaffold)
**Purpose:** the unified "company brain": one Supabase Postgres + pgvector store that holds unstructured content (decks, memos, notes, emails) alongside structured facts, queryable by AI agents (MCP) and the dashboard (REST) through the same service functions.

Tables land in `db/migrations/011_memory_layer.sql`. Code lives in `apps/api/api/memory/` and `apps/api/api/mcp/`.

---

## 1. Design (Sentra-inspired)

1. **Resolve meaning at write time.** `ingest_document` runs one LLM pass per document that extracts structured facts (actors, decisions, commitments, claims) into `memory_facts`, alongside chunk embeddings in `document_chunks`. Agents later query facts directly instead of re-reading raw text.
2. **Bi-temporal-lite.** Facts carry `valid_from` / `valid_until`. When reality changes, the old fact is invalidated (`valid_until` set), never deleted. `get_facts(as_of=...)` answers "what did we believe on date X".
3. **Identity resolution.** `actor_aliases` maps emails/handles/name variants to one canonical `founders` row. `resolve_actor("alex@riveralabs.dev")` returns the founder id.
4. **Provenance first-class.** Every chunk and fact stores `source_type`, `source_locator`, `source_timestamp`. Nothing enters memory without knowing where it came from.

---

## 2. Data access layer (`apps/api/api/memory/`)

| File | Role |
|---|---|
| `store.py` | The ONLY code that touches the 009 tables: `ingest_document`, `search_memory`, `get_facts`, `invalidate_fact`, `resolve_actor` |
| `embeddings.py` | OpenAI `text-embedding-3-small` (1536 dims) wrapper, degrades to `None` without a key |
| `extraction.py` | Write-time fact extraction prompt, reuses `api.intelligence.llm.chat_json` |
| `routes.py` | REST adapter (below) |

Degrade rules match the rest of the codebase: missing OPENAI_API_KEY means chunks store without vectors, search falls back to keyword `ilike`, and fact extraction returns empty. Missing Supabase credentials raise a clean error (REST returns 503). No fabrication, no crashes.

Vector search goes through the `match_document_chunks()` SQL function (defined in 009) via `client.rpc(...)`, because the Supabase REST client cannot order by embedding distance directly.

---

## 3. REST surface (dashboard)

Registered in `main.py` under `/api/v1` like every other router:

| Endpoint | What |
|---|---|
| `POST /api/v1/memory/ingest` | `{title, raw_text, doc_type?, founder_id?, company_id?, source_type?, source_locator?, source_timestamp?}` stores doc + chunks + embeddings + extracted facts |
| `GET/POST /api/v1/memory/search` | Semantic search over chunks (`q` / `{query}`), optional `founder_id` / `company_id` filters, returns chunks with provenance + similarity |
| `GET /api/v1/memory/facts` | Filters: `fact_type`, `subject`, `as_of` (ISO time), `include_invalidated` |

---

## 4. MCP surface (agents)

`apps/api/api/mcp/server.py` is a FastMCP stdio server. Every tool is a thin decorator over the same service functions (no duplicated logic):

| Tool | Wraps |
|---|---|
| `search_memory` | `api.memory.store.search_memory` |
| `get_facts` | `api.memory.store.get_facts` |
| `get_founder_profile` | `api.core.founder_store.get_founder_profile` |
| `screen_opportunity` | `api.ingestion.fast_screen.screen` |

Run it:

```bash
make mcp
# or: cd apps/api && source .venv/bin/activate && python -m api.mcp.server
```

Point Cursor/Claude at that command as a stdio MCP server (env comes from the root `.env` via `api.core.config`).

---

## 5. Product 2 pipelines (`jobs/pipelines/`)

`daily_pipeline.py` is the scheduled-run skeleton: sweep opportunities, fast-screen unscreened ones, run the Analyst -> Validator -> Referee chain on screened passes (capped at 2 per run to bound API spend). It imports existing api modules and owns no logic. Run with `make pipeline`. Scheduling is cron/manual for the hackathon.

---

## 6. Seed data

`db/seed/seed.py` section 9 seeds 2 documents (deck notes + intro call notes for Alex Rivera / Rivera Labs), their chunks, 5 facts, and 3 actor aliases. The seeded `$500K pre-seed` claim has `valid_until` set and is superseded by the `$1.5M seed` claim, so `GET /api/v1/memory/facts?subject=Rivera` demos bi-temporality out of the box.

Seed embeddings are **deterministic fakes** (seeded PRNG vectors) so seeding works offline without an OpenAI key. They upsert idempotently but are not semantically meaningful: for a real semantic-search demo, re-ingest a document through `POST /api/v1/memory/ingest` with a key configured.
