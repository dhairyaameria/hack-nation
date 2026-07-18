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
| [`docs/05-COPILOT-SKILLS.md`](docs/05-COPILOT-SKILLS.md) | Agent D — Thesis Engine, Perplexity, VC Copilot |
| [`docs/06-FRONTEND-UX.md`](docs/06-FRONTEND-UX.md) | Agent E — Investor dashboard & UX |
| [`docs/07-EXECUTION.md`](docs/07-EXECUTION.md) | Milestones, demo script, acceptance checklist |
| [`docs/08-IMPLEMENTATION-PLAN.md`](docs/08-IMPLEMENTATION-PLAN.md) | Time-sequenced build order with gates |
| [`docs/09-NETWORK-GRAPH-UI.md`](docs/09-NETWORK-GRAPH-UI.md) | Founder network graph UI spec (react-force-graph, seed JSON) |

## Parallel build order

1. Read `docs/00-OVERVIEW.md` + `docs/01-CONTRACTS.md`
2. Agent A lands schema first (critical path)
3. Agents B–E work in parallel per `docs/08-IMPLEMENTATION-PLAN.md`
4. Integrate at gates G1–G4 in `docs/07-EXECUTION.md`

## Stack (planned)

Next.js · FastAPI · Supabase · Databricks · OpenAI · Perplexity · Tavily · GraphQL · Wayback Machine
