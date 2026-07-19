# 17: Parallel Workflow (3-Person Team + Coding Agents)

**Audience:** Khaled, Dhairya, Omar, and every coding agent working on this repo
**Purpose:** one source of truth for who owns what, so humans and agents never collide.

This doc supersedes the earlier Agent A-E model. Older docs (02-06, 13) still reference
Agents A-E for task detail. Mapping: A (data) and D (skills) fold into Khaled, B (sourcing)
and C (intelligence) fold into Dhairya, E (frontend) is Omar.

---

## 1. Golden rules

1. **Khaled owns schema.** Nobody else edits `db/migrations/` without his review.
2. **Contract changes require broadcast.** Edit `01-CONTRACTS.md`, notify the group chat,
   update `shared/schemas` and fixtures in the same commit.
3. **One demoable main.** `main` must pass the current gate (G0 to G4) after every merge.
4. **Small PRs / commits.** One task per commit, WHY-first messages.
5. **Never average axes.** Reviewer checks binding rules from `00-OVERVIEW.md` §4 on every merge.
6. **Additive-only contracts.** No renames or removals of existing fields, routes, or tables.

---

## 2. Ownership lanes

### Khaled: Product 1, the company brain (memory + MCP)

| Owns | Notes |
|---|---|
| `apps/api/api/memory/` | Single data-access layer for documents, chunks, facts, aliases |
| `apps/api/api/mcp/` | FastMCP server, the ONE agent connection to the brain |
| `db/migrations/` | Schema owner for the whole team (009+ and reviews) |
| `db/seed/` | Seed data, including memory demo rows |
| `AGENTS.md` (root) | Keeps the agent briefing current |

**Deliverable:** live demo of Claude connected over MCP, answering questions like
"what contradictions did we find in this deck?" with cited provenance.

Note: the memory/MCP modules land via the open `team-k/memory-mcp-scaffold` PR.

### Dhairya: Product 2, the deal pipeline

| Owns | Notes |
|---|---|
| `apps/api/api/intelligence/` | Analyst / Validator / Referee, 3-axis scoring, memos |
| `apps/api/api/ingestion/` | Deck parsing, fast screen, inbound routes |
| `apps/api/api/agent/` | Thesis store and agent chat routes |
| `jobs/pipelines/` | Scheduled end-to-end runs (daily_pipeline.py) |
| `jobs/connectors/` | Outbound sourcing (GitHub, HN, Wayback, Perplexity) |

**Deliverable:** end-to-end inbound and outbound run that writes results into the shared
memory tables, so Product 1 can answer questions about them.

### Omar: UI

| Owns | Notes |
|---|---|
| `apps/web/` | Exclusive. Nobody else edits the frontend |
| `shared/fixtures/` | Keeps fixture IDs aligned with seed data |

**Deliverable:** dashboard wired to real REST endpoints, not just fixtures. Visual polish
comes after live data.

### Arman: to be decided (fill in after onboarding)

Arman joins as the fourth teammate. This lane is intentionally empty until he finishes
onboarding (read `AGENTS.md`, `docs/00-OVERVIEW.md`, `docs/01-CONTRACTS.md`, then this doc)
and picks his focus with the team. Candidate areas, first to last by current need:
outbound connectors under `jobs/connectors/`, the network graph (GraphQL resolvers + UI
handoff with Omar), or demo/QA ownership (seed data, gate checklists, dry runs).

| Owns | Notes |
|---|---|
| _TBD_ | Fill in owned paths here once decided |

**Deliverable:** _TBD, agree with the team and update this section in the same PR as your
first task._

### Shared touchpoints (integrator: Khaled)

| Path | Rule |
|---|---|
| `shared/schemas/` (models.py + types.ts) | Propose in group chat, Khaled applies, everyone pulls |
| `apps/api/main.py` | Router registration only, Khaled applies |
| `docs/01-CONTRACTS.md` | Propose via PR comment, Khaled updates |
| `.cursor/skills/` | Anyone may add, do not rename without updating the router skill |

---

## 3. Branch strategy

```
main            <- always demoable at the latest gate
├── khaled/*    <- memory, MCP, migrations, seed
├── dhairya/*   <- intelligence, ingestion, pipelines, connectors
├── omar/*      <- apps/web, fixtures
└── arman/*     <- TBD after onboarding (see §2)
```

- Branch from fresh `main`, keep branches short-lived (merge every 60 to 90 minutes).
- Merge order at each gate: schema first (Khaled), then API modules (Dhairya),
  then UI (Omar, wired to real endpoints).
- Khaled resolves conflicts in shared files. Never force push.

---

## 4. Cross-imports

Modules communicate via the database and `shared/schemas` only, with two allowed exceptions:

1. Anyone may import `api/intelligence/llm.py` as the shared LLM helper
   (e.g. `api/memory/extraction.py` uses `chat_json`).
2. `jobs/pipelines/` is a thin orchestrator and may import any `api/*` module,
   but must not contain business logic itself.

No other cross-imports between owned modules.

---

## 5. Coding agent dispatch (copy-paste into every agent prompt)

> Read `docs/00-OVERVIEW.md` §4 binding rules and `docs/17-PARALLEL-WORKFLOW.md` §2.
> You are working in [Khaled's | Dhairya's | Omar's] lane. Only edit files inside that
> lane's owned paths. If you need a schema or shared-schema change, describe it in your
> report instead of editing `db/migrations/`, `shared/schemas/`, or `apps/api/main.py`
> yourself. Never average the three axis scores. Attach provenance to every stored fact.

Allowed paths per lane:

- **Khaled's agents:** `apps/api/api/memory/**`, `apps/api/api/mcp/**`, `db/**`, `AGENTS.md`
- **Dhairya's agents:** `apps/api/api/intelligence/**`, `apps/api/api/ingestion/**`,
  `apps/api/api/agent/**`, `jobs/**`
- **Omar's agents:** `apps/web/**`, `shared/fixtures/**`
- **Arman's agents:** _TBD, do not dispatch agents for Arman until his lane in §2 is filled in_

---

## 6. Contract change protocol

1. Proposer describes the field/endpoint in the group chat or PR description.
2. Khaled updates `01-CONTRACTS.md` and `shared/schemas/models.py` + `types.ts`.
3. Khaled migrates if there is DB impact.
4. Omar updates `shared/fixtures/*.json` if UI-visible.
5. Feature PR merges after the contract commit lands.

Additive-only during the hackathon. No renames or removals.

---

## 7. Integration checkpoints

| Gate | Integrator action |
|---|---|
| G0 | Verify API + web boot, `.env` complete |
| G1 | Merge seed, smoke test one founder on dashboard |
| G2 | Merge outbound + validator, run contradiction demo |
| G3 | Merge memory/MCP + agent chat + graph, dry run Claude-over-MCP demo |
| G4 | Full `07-EXECUTION.md` §8 checklist timed twice |

---

## 8. When work conflicts

| Symptom | Fix |
|---|---|
| Duplicate table definitions | Khaled's migration wins, delete the duplicate |
| Different JSON field names | `01-CONTRACTS.md` wins, fix the caller |
| UI expects a field the API does not send | Add optional field to the API (additive) |
| Two people built the same endpoint | Split by path prefix, intelligence vs ingestion vs memory |

---

## 9. Cut order (team agreement)

When behind schedule, stop work on (first to last):

1. Federated module
2. ElevenLabs voice
3. Full-screen network explorer
4. Channel intelligence UI
5. NL query bar polish

**Never cut:** seed contradiction, bias test pair, 3-axis independence, validator,
per-claim trust, thesis switch re-rank, SLA timer, MCP memory demo.

---

## 10. Pre-merge checklist (reviewer)

- [ ] Binding rules §4 in `00-OVERVIEW.md` respected
- [ ] No secrets in diff
- [ ] Fixtures/schemas updated if contract touched
- [ ] Migrations apply clean on fresh DB
- [ ] Only files inside the author's lane (plus approved shared changes) touched
- [ ] `main` still runs the demo path for the current gate
