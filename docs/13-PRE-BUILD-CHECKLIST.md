# 13 — Pre-Build Checklist (Start Here)

Complete this checklist **before** Wave 1 agent work begins.

---

## 1. Read (30 min)

- [ ] `docs/00-OVERVIEW.md` — pipeline + 10 binding rules
- [ ] `docs/01-CONTRACTS.md` — tables + APIs
- [ ] `docs/10-FILTERING-FUNNEL.md` — how companies get filtered
- [ ] `docs/11-ENTITY-MODEL.md` — founder / company / opportunity / thesis
- [ ] `docs/14-SEED-DATA-SPEC.md` — demo characters + stable IDs
- [ ] `docs/17-PARALLEL-WORKFLOW.md` — who owns which folders
- [ ] `docs/08-IMPLEMENTATION-PLAN.md` — Phase 0 + Wave 1

---

## 2. Accounts & keys

- [ ] Supabase project created
- [ ] pgvector extension enabled: `create extension if not exists vector;`
- [ ] Storage bucket `decks` created
- [ ] Copy `.env.example` → `.env` and fill all required keys
- [ ] OpenAI API key (hackathon credits)
- [ ] Perplexity API key
- [ ] Tavily API key
- [ ] (Optional) ElevenLabs, Databricks — skip if behind schedule

---

## 3. Phase 0 scaffold (Gate G0)

- [ ] `apps/api` — FastAPI hello on `:8000`
- [ ] `apps/web` — Next.js hello on `:3000`
- [ ] `shared/schemas/models.py` — EvidenceRef, AxisScore, ClaimTrust, ThesisProfile
- [ ] `db/migrations/` folder exists
- [ ] Supabase connection test passes from API

**Decision:** Postgres-only Bronze/Silver/Gold in Supabase (recommended). Databricks = bonus only.

---

## 4. Agent assignments

| Agent | Doc | Wave 1 task |
|---|---|---|
| A | `02-DATA-FOUNDATION`, `14-SEED-DATA-SPEC`, `16-MIGRATIONS-GUIDE` | Migrations + seed (bias pair, contradiction, 2 theses) |
| B | `03-SOURCING` | Inbound submit + deck parser + fast screen |
| C | `04-INTELLIGENCE-TRUST` | Agent pipeline stubs |
| D | `05-CURSOR-SKILLS` | Thesis CRUD + 2 seed theses |
| E | `06-FRONTEND-UX`, `15-MOCK-FIXTURES` | Dashboard shell + fixtures |

---

## 5. Do NOT build yet (cut if behind)

- [ ] Federated learning module
- [ ] Databricks pipelines
- [ ] Celery/Redis (use FastAPI background tasks)
- [ ] ElevenLabs voice
- [ ] Full GraphQL before REST works

---

## 6. Must ship for demo (protect these)

- [ ] Outbound sourcing + inbound converge to same screen path
- [ ] 3-axis scores independent (never averaged)
- [ ] Validator catches seeded contradiction
- [ ] Per-claim Trust + evidence drill-down
- [ ] Thesis switch re-ranks pipeline
- [ ] SLA timer on decision_log
- [ ] One wow: VC Agent Chat OR network graph OR Wayback

---

## 7. Gate checklist

| Gate | When | Pass criteria |
|---|---|---|
| **G0** | Hour 1 | API + web boot; Supabase connected |
| **G1** | Hour 6 | Seed loads; deck → claims; 1 founder on dashboard |
| **G2** | Hour 14 | Outbound + inbound same funnel; validator catches contradiction |
| **G3** | Hour 22 | Memo + trace + Agent Chat or graph |
| **G4** | Hour 30 | 5-min demo dry run passes `07-EXECUTION` §8 |

---

## 8. First commands (after Phase 0)

```bash
# Terminal 1 — API
cd apps/api && source .venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Web
cd apps/web && npm run dev

# Terminal 3 — Migrations (once Agent A ready)
# apply db/migrations via Supabase SQL editor or psql
python db/seed/seed.py
```

---

## 9. Cursor agent dispatch templates

**Agent A:**
> Read `docs/00-OVERVIEW.md`, `docs/01-CONTRACTS.md`, `docs/11-ENTITY-MODEL.md`, `docs/12-THESIS-SETTINGS-UI.md`, `docs/14-SEED-DATA-SPEC.md`, `docs/16-MIGRATIONS-GUIDE.md`. Implement Wave 1 task 1.A from `docs/08-IMPLEMENTATION-PLAN.md`. Follow module ownership in `docs/17-PARALLEL-WORKFLOW.md`.

**Agent B:**
> Read `docs/03-SOURCING.md`, `docs/10-FILTERING-FUNNEL.md`. Implement Wave 1 task 1.B. Do not edit migrations.

**Agent C:**
> Read `docs/04-INTELLIGENCE-TRUST.md`. Implement Wave 1 task 1.C agent scaffolding only.

**Agent D:**
> Read `docs/05-CURSOR-SKILLS.md`, `docs/12-THESIS-SETTINGS-UI.md`. Implement thesis CRUD + seed 2 profiles.

**Agent E:**
> Read `docs/06-FRONTEND-UX.md`, `docs/12-THESIS-SETTINGS-UI.md`, `docs/15-MOCK-FIXTURES.md`. Build dashboard + thesis settings page against fixtures in `shared/fixtures/`.
