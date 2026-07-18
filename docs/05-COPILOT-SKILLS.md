# 05 — Thesis Engine, Copilot & Skill Repository (Agent D)

**Owner:** Agent D — Copilot
**Depends on:** Agent A's schema; consumes Agent B's sourcing pipeline and Agent C's scoring/memo services as skills.
**PRD sections covered:** §7.1, §7.3, §11.6, Perplexity integration throughout.

---

## Mission

The investor's control surface: a configurable Thesis Engine with Perplexity-powered live research, compound natural-language queries, and a VC Copilot chatbot routing over a versioned skill repository so any question is answerable, citable, and repeatable.

## 1. Thesis Engine

- CRUD (`POST /thesis`, `GET /thesis/{id}`) for versioned thesis profiles: sectors, stage, geography, check size, ownership targets, risk appetite. Multiple profiles per fund. **Configurable, never hardcoded.**
- Thesis parameterizes: candidate ranking, watchlist promotion thresholds (Agent B reads this), memo emphasis (Agent C reads this — e.g., risk-averse thesis surfaces bear-case more prominently).
- Versioned storage so historical recommendations can be replayed against a new thesis.

## 2. Perplexity-Powered Thesis Research

- Compile the active thesis into structured research queries against the **Perplexity API** (search-grounded, native citations).
- Recurring sourcing sweeps: recent launches, hiring posts, hackathon results, community mentions matching the thesis lens.
- Results land in Bronze via Agent B's `ingest_raw` (`source = perplexity`, query text, citations, timestamp) — watchlist candidates, NOT pre-trusted facts.
- Native citations attach directly as `EvidenceRef`s — no separate retrieval pass needed.

## 3. Multi-Attribute Natural-Language Query (`POST /query/natural-language`)

- One-pass resolution of compound queries, e.g. *"technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator."*
- Decompose into structured constraints (location, technical background, sector, traction, funding history, program pedigree) → ranked result set.
- Each result explains *why* it matched each clause. Not five sequential filters.

## 4. Skill Repository

Versioned definitions in `skill_definitions` (contract format in `01-CONTRACTS.md` §4). Initial catalog:

| Skill | What it does | Backing |
|---|---|---|
| `thesis_sourcing_sweep` | Live web research from active thesis; returns leads with citations | Perplexity → Bronze |
| `memo_research` | Market sizing, competitor clusters, comparable rounds for a target | Perplexity, Tavily |
| `generate_memo` | Full memo (required sections + gap flags) | Agent C's pipeline |
| `verify_claim` | On-demand validator pass on one claim | Agent C's validator |
| `founder_genome_lookup` | Genome dimensions + trends + evidence | Gold features |
| `network_proximity_check` | 2nd-degree paths to anchors + disclosure | Agent B's GraphQL |
| `wayback_history` | Historical narrative/sentiment for a domain | Agent B's Wayback module |
| `screen_opportunity` | Fast first-pass screen | Agent B's screening |
| `channel_quality_report` | Channel ranking + underexplored suggestions | Agent B's channel intel |
| `compare_opportunities` | Side-by-side 3-axis + trust comparison | Agent C's scores |

Note most skills WRAP other agents' services — build thin adapters, don't reimplement logic.

## 5. VC Copilot Chatbot (`POST /copilot/message`)

- **Router agent** (OpenAI tool-calling): maps each investor question to one or more skills. Examples:
  - "Should I worry about the ARR claim in Acme's deck?" → `verify_claim`
  - "Find me three more founders like this one" → `thesis_sourcing_sweep` + `founder_genome_lookup`
- **No-match honesty:** if no skill matches, say so explicitly — never free-style an unsourced answer.
- **Composition:** skills chain within one turn (research → verify → summarize).
- **Repeatability:** every execution logged as `skill_run` (skill id+version, inputs, snapshot refs, output, citations, timestamp). `POST /skill-runs/{id}/rerun` re-executes against fresh data and returns a diff vs. the prior answer.
- **Traceability:** every factual statement carries an `EvidenceRef`; skill runs write into `reasoning_traces`.
- **Versioning:** improving a skill bumps its version; historical runs keep their original version's meaning.

## 6. Endpoints Owned

`/thesis*`, `/query/natural-language`, `/copilot/message`, `/skills*`, `/skill-runs*` (full list in `01-CONTRACTS.md` §2).

## Acceptance Checks

- [ ] Two thesis profiles; switching the active thesis changes top recommendations live.
- [ ] Perplexity sweep produces provenance-tagged Bronze leads with citations attached.
- [ ] Compound NL query resolved in one pass with per-clause match explanations.
- [ ] Copilot routes a free-form question to the right skill(s), shows skill names + citations in the answer.
- [ ] At least one Perplexity-backed research skill runs end-to-end in chat.
- [ ] Re-run of a prior question returns a diff against the previous answer.
- [ ] Unanswerable question gets an explicit "no matching skill" response, not a hallucinated answer.
