# VC Brain

**A data- and AI-first venture operating system: sources founders before they raise, scores them on three independent axes, and produces a $100K yes/no recommendation in under 24 hours — with a traceable source behind every claim.**

Built for [The VC Brain challenge](1784381921507-02-Maschmeyer-Group-The-VC-Brain.docx.pdf) (Maschmeyer Group × Hack-Nation).

## The problem

Early-stage investing has three failures that compound each other:

- **You meet founders too late.** The strongest signals — a founder shipping relentlessly on GitHub, a first-author paper, a hackathon win — are public long before a raise, but nobody systematically watches them.
- **Diligence doesn't scale, so it gets skipped.** Under time pressure it collapses into gut feel plus whoever vouched for the founder — which is how bias enters, and how cold-start founders with thin networks get filtered out for the wrong reason.
- **AI tools hide uncertainty.** A single confident score with no traceable reasoning can't be audited or argued with. A wrong number delivered confidently is more dangerous than no number.

VC Brain's core bet: **speed and rigour can be compatible.** The 24-hour decision should be *more* auditable than a two-week one, not less.

## What it does

The system covers the full funnel — **Sourcing → Screening → Diligence → Decision** — with a persistent memory layer underneath.

- **Outbound sourcing before the raise.** Live connectors for GitHub, Hacker News, arXiv, and LinkedIn, plus Perplexity and Tavily for search-grounded research. Candidates move through a watchlist state machine (`discovered → scored → activation-candidate → outreach-sent → applied`), and promotion requires corroboration from more than one signal.
- **Near-zero-friction inbound.** Founders submit a deck and a company name — no 40-field form. The deck is parsed, claims are extracted with pointers back to the slide they came from, and a fast thesis screen (Perplexity-reranked) prioritizes the queue.
- **Three independent axes, never averaged.** Founder, Market, and Idea-vs-Market are computed, stored, and displayed separately, each with its own trend. There is no composite score anywhere in the UI, API, or memos — disagreement between axes stays visible instead of being smoothed into one misleading number.
- **Per-claim trust, not per-company.** An Analyst → Validator → Referee agent chain cross-checks each claim against independent sources. When a deck claims $1.2M ARR and the Stripe export says $412K, the memo shows both side by side.
- **Memos that mark their own gaps.** Missing data is flagged, never fabricated — and the system distinguishes *not disclosed* (the founder withheld it) from *unknown* (we searched and couldn't confirm).
- **Cold-start founders are first-class.** Absence of network signal is scored as *unknown*, never as *bad*, and network proximity is capped within the Founder axis with plain-language disclosure.
- **Persistent memory + agent access.** A Founder Score that follows the person across applications, and a fact store (validity windows, embeddings) queryable by the dashboard *and* by external AI agents over MCP — one brain, not two.
- **Ask by voice.** Investors can ask the demo questions by voice — mic input transcribed via ElevenLabs, answered by the agent with cited sources.

## Architecture

```
apps/web    Next.js 16 (App Router, React 19, TS, Tailwind v4, shadcn/ui) — investor dashboard
apps/api    FastAPI (Python) — domains: ingestion, intelligence, memory, agent, graphql, mcp
db/         Ordered SQL migrations (Supabase Postgres + pgvector) + demo seed
jobs/       Scheduled pipelines: daily sourcing/analysis sweep, Perplexity inbound rerank
shared/     Shared contracts
docs/       Full specification set (see below)
```

**Stack:** Next.js · FastAPI · Supabase (Postgres + pgvector, Auth, Storage) · OpenAI · Perplexity · Tavily · ElevenLabs · GraphQL · Wayback Machine CDX · FastMCP · Vercel (web) · Render/Docker (API)

Every ingested record carries provenance (`source`, `source_entity_id`, `fetched_at`, `run_id`), organized in a Bronze/Silver/Gold separation between raw records, resolved entities, and computed features.

## Quick start

Prereqs: Node 20+, Python 3.11+, a Supabase project, and API keys for OpenAI, Perplexity, and Tavily (ElevenLabs optional, for voice input).

```bash
# 1. Configure
cp .env.example .env   # fill in Supabase + API keys

# 2. Install
cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ../..
cd apps/web && npm install && cd ../..

# 3. Database (applies db/migrations/*.sql in order, then demo seed)
make db-reset
make db-seed

# 4. Run — API on :8000, web on :3000
make dev
```

Other entry points:

```bash
make mcp             # MCP server (stdio) — agents' entry point to the memory layer
make pipeline        # daily loop: screen + analyze seeded opportunities
make inbound-rerank  # Perplexity inbound rerank (same code path as POST /api/v1/inbound/rerank)
```

The frontend can also run without a live backend: set `NEXT_PUBLIC_USE_FIXTURES=true` to serve the dashboard from bundled JSON fixtures.

## Binding rules

These are enforced in the product, not aspirations:

1. **No composite score** — the three axes are never averaged, anywhere.
2. **Per-claim trust** — evidence, confidence, and validation status attach to claims, not companies.
3. **Gaps are never fabricated** — a memo says what it doesn't know, and distinguishes *not disclosed* from *unknown*.
4. **Absence of network signal is scored as unknown, never negative.**

## Documentation

Start with [`docs/00-OVERVIEW.md`](docs/00-OVERVIEW.md) (shared context and pipeline) and [`VC_Brain_PRD.md`](VC_Brain_PRD.md) (master PRD). Submission answers live in [`SUBMISSION.md`](SUBMISSION.md).

<details>
<summary>Full spec set (docs/)</summary>

| Document | Purpose |
|---|---|
| [`docs/00-OVERVIEW.md`](docs/00-OVERVIEW.md) | Shared context, pipeline, binding rules — read first |
| [`docs/01-CONTRACTS.md`](docs/01-CONTRACTS.md) | Data model, REST/GraphQL contracts, repo structure |
| [`docs/02-DATA-FOUNDATION.md`](docs/02-DATA-FOUNDATION.md) | Memory layer, Supabase, Bronze/Silver/Gold |
| [`docs/03-SOURCING.md`](docs/03-SOURCING.md) | Inbound/outbound sourcing, network, Wayback |
| [`docs/04-INTELLIGENCE-TRUST.md`](docs/04-INTELLIGENCE-TRUST.md) | 3-axis scoring, trust, memos, agents |
| [`docs/05-CURSOR-SKILLS.md`](docs/05-CURSOR-SKILLS.md) | Thesis Engine, Perplexity, Cursor Skills, VC Agent Chat |
| [`docs/06-FRONTEND-UX.md`](docs/06-FRONTEND-UX.md) | Investor dashboard & UX |
| [`docs/07-EXECUTION.md`](docs/07-EXECUTION.md) | Milestones, demo script, acceptance checklist |
| [`docs/08-IMPLEMENTATION-PLAN.md`](docs/08-IMPLEMENTATION-PLAN.md) | Time-sequenced build order with gates |
| [`docs/09-NETWORK-GRAPH-UI.md`](docs/09-NETWORK-GRAPH-UI.md) | Founder network graph UI spec |
| [`docs/10-FILTERING-FUNNEL.md`](docs/10-FILTERING-FUNNEL.md) | How companies get filtered (thesis + funnel) |
| [`docs/11-ENTITY-MODEL.md`](docs/11-ENTITY-MODEL.md) | Founder / company / opportunity / thesis model |
| [`docs/12-THESIS-SETTINGS-UI.md`](docs/12-THESIS-SETTINGS-UI.md) | VC thesis profile schema + Settings UI |
| [`docs/13-PRE-BUILD-CHECKLIST.md`](docs/13-PRE-BUILD-CHECKLIST.md) | Pre-build checklist |
| [`docs/14-SEED-DATA-SPEC.md`](docs/14-SEED-DATA-SPEC.md) | Demo seed catalog (IDs, bias pair, contradiction) |
| [`docs/15-MOCK-FIXTURES.md`](docs/15-MOCK-FIXTURES.md) | Frontend JSON fixtures |
| [`docs/16-MIGRATIONS-GUIDE.md`](docs/16-MIGRATIONS-GUIDE.md) | Ordered SQL migrations |
| [`docs/17-PARALLEL-WORKFLOW.md`](docs/17-PARALLEL-WORKFLOW.md) | Multi-agent branches, ownership, merge order |
| [`docs/18-MEMORY-LAYER.md`](docs/18-MEMORY-LAYER.md) | Memory layer (company brain), MCP server, pipelines |
| [`docs/19-INBOUND-RERANK.md`](docs/19-INBOUND-RERANK.md) | Perplexity inbound rerank (API + cron, cost notes) |

</details>

## Deployment

- **Web:** Vercel ([`apps/web/vercel.json`](apps/web/vercel.json))
- **API:** Render via Docker ([`render.yaml`](render.yaml)) — set env vars from `.env.example`, health check at `/health`
