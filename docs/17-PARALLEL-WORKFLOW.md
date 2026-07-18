# 17 — Parallel Workflow (Multi-Agent Build)

**Audience:** human team + Cursor agents working in parallel  
**Purpose:** avoid merge conflicts, contract drift, and duplicate work during the hackathon.

---

## 1. Golden rules

1. **Agent A owns schema.** No other agent edits `db/migrations/` without A's review.
2. **Contract changes require broadcast.** Edit `01-CONTRACTS.md` → notify all agents → update `shared/schemas` + fixtures same commit.
3. **One demoable main.** `main` must pass the current gate (G0→G4) after every merge.
4. **Small PRs / commits.** One task ID per commit (e.g. `1.A migrations 002-003`, `1.E dashboard fixtures`).
5. **Never average axes.** Reviewer checks binding rules from `00-OVERVIEW.md` §4 on every merge.

---

## 2. Branch strategy

```
main                 ← always demoable at latest gate
├── agent/a-data     ← migrations, seed, ingestion
├── agent/b-source   ← application, connectors, watchlist
├── agent/c-intel    ← scoring, validator, memos
├── agent/d-skills   ← thesis, agent chat, skills
└── agent/e-frontend ← Next.js UI
```

**Merge order at each gate:**

1. Agent A → main (schema + seed first)
2. Agents D, B, C in any order (API modules)
3. Agent E last (UI wired to real endpoints)

Integrator (team lead) resolves conflicts in `shared/schemas` and `01-CONTRACTS.md`.

---

## 3. Module ownership (API)

```
apps/api/
  api/ingestion/      → Agent B only
  api/intelligence/   → Agent C only
  api/agent/          → Agent D only
  api/graphql/        → Agent B (resolvers)
  main.py             → integrator (route registration only)
```

Do not create cross-imports between agent modules — communicate via DB + shared schemas only.

---

## 4. Shared touchpoints (high conflict zones)

| Path | Owner | Others |
|---|---|---|
| `db/migrations/` | A | read-only |
| `db/seed/` | A | suggest data in `14-SEED-DATA-SPEC.md` |
| `shared/schemas/` | integrator | all agents propose changes |
| `shared/fixtures/` | E | A/C keep IDs aligned with seed |
| `.cursor/skills/` | D | don't rename without updating router |
| `01-CONTRACTS.md` | integrator | propose via PR comment |

---

## 5. Cursor agent dispatch (copy-paste)

Include in every agent prompt:

> Read `00-OVERVIEW.md` §4 binding rules. Do not edit files outside your module ownership in `17-PARALLEL-WORKFLOW.md`. If you need a schema change, describe it in a comment — do not edit migrations yourself (unless you are Agent A).

Full dispatch templates: `13-PRE-BUILD-CHECKLIST.md` §9.

---

## 6. Contract change protocol

1. Agent proposes field/endpoint in PR description
2. Integrator updates `01-CONTRACTS.md`
3. Agent A migrates if DB impact
4. Update `shared/schemas/models.py` + `types.ts`
5. Update `shared/fixtures/*.json` if UI-visible
6. Merge agent feature PR

**Additive-only during hackathon** — no renames/removals after Wave 1 starts.

---

## 7. Integration checkpoints

| Gate | Integrator action |
|---|---|
| G0 | Verify API + web boot, `.env` complete |
| G1 | Merge A seed → smoke test one founder on dashboard |
| G2 | Merge B outbound + C validator → run contradiction demo |
| G3 | Merge D agent chat + E graph → dry run trace + chat |
| G4 | Full `07-EXECUTION.md` §8 checklist timed twice |

---

## 8. When agents conflict

| Symptom | Fix |
|---|---|
| Duplicate table definitions | A wins; delete duplicate migration |
| Different JSON field names | Contracts doc wins; fix caller |
| UI expects field API doesn't send | Add optional field to API (additive) |
| Two agents built same endpoint | Keep C's for intelligence, B's for sourcing — split by path prefix |

---

## 9. Cut order (team agreement)

When behind schedule, stop work on (first → last):

1. Federated module
2. ElevenLabs voice
3. Full-screen network explorer
4. Channel intelligence UI
5. NL query bar polish

**Never cut:** seed contradiction, bias test pair, 3-axis independence, validator, per-claim trust, thesis switch re-rank, SLA timer.

---

## 10. Pre-merge checklist (reviewer)

- [ ] Binding rules §4 in `00-OVERVIEW.md` respected
- [ ] No secrets in diff
- [ ] Fixtures/schemas updated if contract touched
- [ ] Migrations apply clean on fresh DB
- [ ] `main` still runs demo path for current gate
