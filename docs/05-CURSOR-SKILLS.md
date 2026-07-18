# 05 — Thesis Engine, Cursor Skills & VC Agent Chat (Agent D)

**Owner:** Agent D — Cursor Skills
**Depends on:** Agent A's schema; consumes Agent B's sourcing pipeline and Agent C's scoring/memo services.
**PRD sections covered:** §7.1, §7.3, §11.6, Perplexity integration throughout.

---

## Mission

The investor's control surface: a configurable Thesis Engine with Perplexity-powered live research, compound natural-language queries, and a **VC Agent Chat** that routes questions through a **Cursor Skills repository** — project-scoped Agent Skills in `.cursor/skills/` — so every capability is reusable, versioned, citable, and repeatable.

**Why Cursor Skills (not a custom copilot catalog):**
- Skills are **first-class Cursor Agent Skills** (`SKILL.md` + YAML frontmatter) — the same skills your team uses in Cursor to build, and the runtime agent uses in the product.
- Single source of truth: `.cursor/skills/<skill-name>/SKILL.md`.
- At runtime, the API **loads skill metadata from disk**, executes the skill's procedure via tool bindings, and logs each run to `skill_runs` for repeatability and demo diffing.

---

## 1. Thesis Engine

- CRUD (`POST /thesis`, `GET /thesis/{id}`) for versioned thesis profiles: sectors, stage, geography, check size, ownership targets, risk appetite. Multiple profiles per fund. **Configurable, never hardcoded.**
- Thesis parameterizes: candidate ranking, watchlist promotion thresholds (Agent B reads this), memo emphasis (Agent C reads this — e.g., risk-averse thesis surfaces bear-case more prominently).
- Versioned storage so historical recommendations can be replayed against a new thesis.

## 2. Perplexity-Powered Thesis Research

- Compile the active thesis into structured research queries against the **Perplexity API** (search-grounded, native citations).
- Recurring sourcing sweeps: recent launches, hiring posts, hackathon results, community mentions matching the thesis lens.
- Results land in Bronze via Agent B's `ingest_raw` (`source = perplexity`, query text, citations, timestamp) — watchlist candidates, NOT pre-trusted facts.
- Implemented as Cursor skill: `.cursor/skills/thesis-sourcing-sweep/SKILL.md`.

## 3. Multi-Attribute Natural-Language Query (`POST /query/natural-language`)

- One-pass resolution of compound queries, e.g. *"technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator."*
- Decompose into structured constraints → ranked result set with per-clause match explanations.

## 4. Cursor Skills Repository

### 4.1 Location & format

```
.cursor/skills/
├── thesis-sourcing-sweep/SKILL.md
├── memo-research/SKILL.md
├── generate-memo/SKILL.md
├── verify-claim/SKILL.md
├── founder-genome-lookup/SKILL.md
├── network-proximity-check/SKILL.md
├── wayback-history/SKILL.md
├── screen-opportunity/SKILL.md
├── channel-quality-report/SKILL.md
├── compare-opportunities/SKILL.md
└── vc-agent-router/SKILL.md      # maps investor questions → skills
```

Each `SKILL.md` follows [Cursor Agent Skills format](https://cursor.com/docs): YAML frontmatter (`name`, `description`) + procedural instructions + tool/API bindings.

### 4.2 Skill catalog

| Cursor skill | What it does | Backing |
|---|---|---|
| `thesis-sourcing-sweep` | Live web research from active thesis; returns leads with citations | Perplexity → Bronze |
| `memo-research` | Market sizing, competitors, comparable rounds | Perplexity, Tavily |
| `generate-memo` | Full memo (required sections + gap flags) | Agent C pipeline |
| `verify-claim` | On-demand validator pass on one claim | Agent C validator |
| `founder-genome-lookup` | Genome dimensions + trends + evidence | Gold features |
| `network-proximity-check` | 2nd-degree paths to anchors + disclosure | Agent B GraphQL |
| `wayback-history` | Historical narrative/sentiment for a domain | Agent B Wayback |
| `screen-opportunity` | Fast first-pass screen | Agent B screening |
| `channel-quality-report` | Channel ranking + underexplored suggestions | Agent B channel intel |
| `compare-opportunities` | Side-by-side 3-axis + trust comparison | Agent C scores |
| `vc-agent-router` | Routes NL investor questions to the right skill(s) | OpenAI tool-calling |

Most skills **wrap** other agents' services — thin adapters, don't reimplement logic.

### 4.3 Runtime sync (API)

- On startup (or on demand), `apps/api/api/agent/skill_loader.py` scans `.cursor/skills/*/SKILL.md`, parses frontmatter, and registers skills in memory (optional mirror to `skill_definitions` table for versioning audit).
- `skill_runs` table logs every execution: skill name, inputs, snapshot refs, output, citations, timestamp — enables re-run + diff in the UI.

## 5. VC Agent Chat (`POST /agent/message`)

Investor-facing chat panel (not "Copilot") — routes through Cursor Skills:

- **Router:** uses `vc-agent-router` skill + OpenAI tool-calling to pick one or more skills per question.
  - *"Should I worry about the ARR claim?"* → `verify-claim`
  - *"Find me three more founders like this one"* → `thesis-sourcing-sweep` + `founder-genome-lookup`
- **No-match honesty:** if no skill matches, say so explicitly — never free-style an unsourced answer.
- **Composition:** skills chain within one turn (research → verify → summarize).
- **Repeatability:** `POST /skill-runs/{id}/rerun` re-executes against fresh Memory data and returns a diff.
- **Traceability:** every factual statement carries an `EvidenceRef`; runs write to `reasoning_traces`.
- **UI shows which Cursor skill(s) ran** — skill folder name visible in the answer (demo-friendly).

## 6. Endpoints Owned

`/thesis*`, `/query/natural-language`, `/agent/message`, `/skills*`, `/skill-runs*` (full list in `01-CONTRACTS.md` §2).

## 7. Building with Cursor (dev workflow)

When implementing Agent D tasks in Cursor IDE:
1. Open the relevant skill: e.g. `.cursor/skills/verify-claim/SKILL.md`
2. Agent auto-applies the skill when the task matches its `description`
3. Implement the FastAPI handler that executes the skill's procedure
4. Test via `POST /skills/verify-claim/run` then via `POST /agent/message`

## Acceptance Checks

- [ ] All 10+ skills exist as `SKILL.md` files under `.cursor/skills/`
- [ ] Two thesis profiles; switching active thesis changes top recommendations live
- [ ] Perplexity sweep produces provenance-tagged Bronze leads with citations
- [ ] Compound NL query resolved in one pass with per-clause explanations
- [ ] VC Agent Chat routes a free-form question to the right Cursor skill(s), shows skill names + citations
- [ ] At least one Perplexity-backed skill runs end-to-end in chat
- [ ] Re-run of a prior question returns a diff against the previous answer
- [ ] Unanswerable question gets explicit "no matching skill" response
