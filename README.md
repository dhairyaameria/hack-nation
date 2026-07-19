# VC Brain — Hack-Nation

Data- and AI-first venture operating system for discovering founders, running diligence, and producing $100K investment recommendations within 24 hours.

**Challenge:** [The VC Brain — Maschmeyer Group × Hack-Nation](1784381921507-02-Maschmeyer-Group-The-VC-Brain.docx.pdf)

## Documentation

| Document | Purpose |
|---|---|
| [`VC_Brain_PRD.md`](VC_Brain_PRD.md) | Master product requirements (authoritative) |
| [`docs/00-OVERVIEW.md`](docs/00-OVERVIEW.md) | Shared context, pipeline, binding rules — read first |
| [`docs/01-CONTRACTS.md`](docs/01-CONTRACTS.md) | Data model, REST/GraphQL contracts, repo structure |
| [`docs/02-DATA-FOUNDATION.md`](docs/02-DATA-FOUNDATION.md) | Agent A — Memory layer, Supabase, Bronze/Silver/Gold |
| [`docs/03-SOURCING.md`](docs/03-SOURCING.md) | Agent B — Inbound/outbound sourcing, network, Wayback |
| [`docs/04-INTELLIGENCE-TRUST.md`](docs/04-INTELLIGENCE-TRUST.md) | Agent C — 3-axis scoring, trust, memos, agents |
| [`docs/05-CURSOR-SKILLS.md`](docs/05-CURSOR-SKILLS.md) | Agent D — Thesis Engine, Perplexity, Cursor Skills, VC Agent Chat |
| [`docs/06-FRONTEND-UX.md`](docs/06-FRONTEND-UX.md) | Agent E — Investor dashboard & UX |
| [`docs/07-EXECUTION.md`](docs/07-EXECUTION.md) | Milestones, demo script, acceptance checklist |
| [`docs/08-IMPLEMENTATION-PLAN.md`](docs/08-IMPLEMENTATION-PLAN.md) | Time-sequenced build order with gates |
| [`docs/09-NETWORK-GRAPH-UI.md`](docs/09-NETWORK-GRAPH-UI.md) | Founder network graph UI spec (react-force-graph, seed JSON) |
| [`docs/10-FILTERING-FUNNEL.md`](docs/10-FILTERING-FUNNEL.md) | How companies get filtered (thesis + funnel) |
| [`docs/11-ENTITY-MODEL.md`](docs/11-ENTITY-MODEL.md) | Founder / company / opportunity / thesis model |
| [`docs/12-THESIS-SETTINGS-UI.md`](docs/12-THESIS-SETTINGS-UI.md) | VC thesis profile schema + Settings UI |
| [`docs/13-PRE-BUILD-CHECKLIST.md`](docs/13-PRE-BUILD-CHECKLIST.md) | **Pre-build checklist — start here** |
| [`docs/14-SEED-DATA-SPEC.md`](docs/14-SEED-DATA-SPEC.md) | Demo seed catalog (IDs, bias pair, contradiction) |
| [`docs/15-MOCK-FIXTURES.md`](docs/15-MOCK-FIXTURES.md) | Wave 1 frontend JSON fixtures |
| [`docs/16-MIGRATIONS-GUIDE.md`](docs/16-MIGRATIONS-GUIDE.md) | Ordered SQL migrations (Agent A) |
| [`docs/17-PARALLEL-WORKFLOW.md`](docs/17-PARALLEL-WORKFLOW.md) | Multi-agent branches, ownership, merge order |
| [`docs/19-INBOUND-RERANK.md`](docs/19-INBOUND-RERANK.md) | Perplexity inbound rerank (API + cron, cost notes) |

## Quick start

1. Complete [`docs/13-PRE-BUILD-CHECKLIST.md`](docs/13-PRE-BUILD-CHECKLIST.md)
2. Copy [`.env.example`](.env.example) → `.env`
3. Read `docs/00-OVERVIEW.md` + `docs/01-CONTRACTS.md`
4. Run Phase 0 in `docs/08-IMPLEMENTATION-PLAN.md`

## Parallel build order

1. Read `docs/00-OVERVIEW.md` + `docs/01-CONTRACTS.md`
2. Agent A lands schema first (critical path)
3. Agents B–E work in parallel per `docs/08-IMPLEMENTATION-PLAN.md`
4. Integrate at gates G1–G4 in `docs/07-EXECUTION.md`

## Stack (planned)

Next.js · FastAPI · Supabase · Databricks · OpenAI · Perplexity · Tavily · GraphQL · Wayback Machine · **Cursor Skills** (`.cursor/skills/`)
